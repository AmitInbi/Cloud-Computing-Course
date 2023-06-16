from flask import Flask, request, jsonify
import threading
from queue import Queue
from datetime import datetime, timedelta
import subprocess
import requests
import json
import time


app = Flask(__name__)

workQueue = Queue()
workComplete = Queue()
maxNumOfWorkers = 1
# TODO: add workers^^
numOfWorkers = 0
otherManager = None
lastWorkerSpawned = datetime.now()


def check_if_need_more_workers():
    global workQueue, workComplete, maxNumOfWorkers, numOfWorkers, otherManager, lastWorkerSpawned
    print("###########timer tick###########")
    print(f"Object Status:\n"
          f"Current time: {datetime.now()}\n"
          f"workQueue size: {workQueue.qsize()}\n"
          f"workComplete size: {workComplete.qsize()}\n"
          f"maxNumOfWorkers: {maxNumOfWorkers}\n"
          f"numOfWorkers: {numOfWorkers}\n"
          f"lastWorkerSpawned: {lastWorkerSpawned}\n"
          f"thread: {threading.current_thread()}\n"
          f"otherManager: {otherManager}")

    if not workQueue.empty():
        work_item = workQueue.queue[0]
        # Check new worker wasn't already spawned in last 3 minutes (average up time)
        if datetime.now() - lastWorkerSpawned > timedelta(seconds=180):
            # check if work_item wasn't created is in queue for more than 30 seconds
            # TODO: if datetime.now() - work_item[2] > timedelta(seconds=30):
            if datetime.now() - work_item[2] > timedelta(seconds=1):
                if numOfWorkers < maxNumOfWorkers:
                    spawnWorker()
                else:
                    if otherManager.TryGetNodeQuota():
                        maxNumOfWorkers += 1


def spawnWorker():
    global workQueue, workComplete, maxNumOfWorkers, numOfWorkers, otherManager, lastWorkerSpawned
    lastWorkerSpawned = datetime.now()
    try:
        subprocess.run(['bash', 'setup_worker.sh', otherManager], check=True)
        print("spawnWorker")
    except subprocess.CalledProcessError as e:
        print(f"Failed to spawn worker: {e}")


def TryGetNodeQuota(otherManager):
    global workQueue, workComplete, maxNumOfWorkers, numOfWorkers, lastWorkerSpawned
    return requests.get(f"{otherManager}/TryGetNodeQuota")


def enqueueWork(data, iterations):
    global workQueue, workComplete, maxNumOfWorkers, numOfWorkers, otherManager, lastWorkerSpawned
    workQueue.put((data, iterations, datetime.now()))


def giveMeWork():
    global workQueue, workComplete, maxNumOfWorkers, numOfWorkers, otherManager, lastWorkerSpawned
    return workQueue.get() or None


def completed(result):
    global workQueue, workComplete, maxNumOfWorkers, numOfWorkers, otherManager, lastWorkerSpawned
    workComplete.put(result)


def pullComplete(top):
    global workQueue, workComplete, maxNumOfWorkers, numOfWorkers, otherManager, lastWorkerSpawned

    result = []
    for i in range(top):
        if not workComplete.empty():
            result.append(workComplete.get())
        else:
            break
    if len(result) < top:
        missing_completed = str(top - len(result))
        url = f"http://{otherManager}/pullCompleteInternal?top={missing_completed}"
        response = requests.get(url)
        result.append(json.loads(response))
    return result


def pullCompleteInternal(top):
    global workQueue, workComplete, maxNumOfWorkers, numOfWorkers, otherManager, lastWorkerSpawned

    result = []
    for i in range(top):
        if not workComplete.empty():
            result.append(workComplete.get())
        else:
            break
    return result


@app.route('/enqueue', methods=['PUT'])
def enqueue():
    global workQueue, workComplete, maxNumOfWorkers, numOfWorkers, otherManager, lastWorkerSpawned

    iterations = int(request.args.get('iterations'))
    data = request.get_data(as_text=True)
    enqueueWork(data, iterations)
    return 'Work enqueued successfully'


@app.route('/pullCompleted', methods=['POST'])
def pull_completed():
    global workQueue, workComplete, maxNumOfWorkers, numOfWorkers, otherManager, lastWorkerSpawned

    top = int(request.args.get('top'))
    results = pullComplete(top)
    return jsonify(results)


@app.route('/internal/pullCompleteInternal', methods=['GET'])
def pull_complete_internal():
    global workQueue, workComplete, maxNumOfWorkers, numOfWorkers, otherManager, lastWorkerSpawned

    top = int(request.args.get('top'))
    results = pullCompleteInternal(top)
    return jsonify(results)


@app.route('/internal/giveMeWork', methods=['GET'])
def give_me_work():
    global workQueue, workComplete, maxNumOfWorkers, numOfWorkers, otherManager, lastWorkerSpawned

    work_item = giveMeWork()
    if work_item:
        return jsonify(work_item), 200
    else:
        return jsonify({'message': 'No available work'}), 404


@app.route('/internal/sendCompletedWork', methods=['POST'])
def send_completed_work():
    global workQueue, workComplete, maxNumOfWorkers, numOfWorkers, otherManager, lastWorkerSpawned

    # Get the completed work from the request
    result = request.get_json()
    completed(result)
    return 'Completed work added successfully'


@app.route('/addSibling', methods=['POST'])
def add_sibling():
    global workQueue, workComplete, maxNumOfWorkers, numOfWorkers, otherManager, lastWorkerSpawned

    manager = request.args.get('manager')
    otherManager = manager
    return 'Sibling added successfully'


@app.route('/internal/TryGetNodeQuota', methods=['GET'])
def try_get_node_quota():
    global workQueue, workComplete, maxNumOfWorkers, numOfWorkers, otherManager, lastWorkerSpawned

    if numOfWorkers < maxNumOfWorkers:
        maxNumOfWorkers -= 1
        return True
    return False


def period():
    print("Period!###############################")

    global workQueue, workComplete, maxNumOfWorkers, numOfWorkers, otherManager, lastWorkerSpawned
    global mainThreadFlag
    while True:
        check_if_need_more_workers()
        time.sleep(5)


app_thread = threading.Thread(target=period)
app_thread.start()
app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
