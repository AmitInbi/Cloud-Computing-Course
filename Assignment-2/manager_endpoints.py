from flask import Flask, request, jsonify
import threading
from queue import Queue
from datetime import datetime, timedelta
import subprocess
import requests
import json
import time
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(filename='manager.log', level=logging.INFO)

workQueue = Queue()
workComplete = Queue()
maxNumOfWorkers = 1
# TODO: add workers^^
numOfWorkers = 0
otherManager = None
lastWorkerSpawned = datetime.now()


def check_if_need_more_workers():
    global workQueue, workComplete, maxNumOfWorkers, numOfWorkers, otherManager, \
        lastWorkerSpawned
    logging.info("###########timer tick###########")
    logging.info(f"Object Status:\n"
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
                if numOfWorkers <= maxNumOfWorkers:
                    logging.info("Spawning a new worker")
                    spawnWorker()
                else:
                    if TryGetNodeQuota():
                        maxNumOfWorkers += 1
                        logging.info("Incrementing maxNumOfWorkers")


def spawnWorker():
    global numOfWorkers, otherManager, lastWorkerSpawned
    lastWorkerSpawned = datetime.now()
    try:
        numOfWorkers += 1
        subprocess.run(['bash', 'setup_worker.sh', otherManager], check=True)
        logging.info("Worker spawned successfully")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to spawn worker: {e}")


def TryGetNodeQuota():
    global otherManager
    # TODO: Uncomment this \/
    # return requests.get(f"{otherManager}/TryGetNodeQuota")
    return False


def enqueueWork(data, iterations):
    global workQueue
    workQueue.put((data, iterations, datetime.now()))
    logging.info("Work enqueued successfully")


def giveMeWork():
    global workQueue
    work_item = workQueue.get()
    if work_item:
        logging.info("Work dequeued successfully")
        return work_item
    else:
        logging.info("No available work in the queue")
        return None


def completed(result):
    global workComplete
    workComplete.put(result)
    logging.info("Work completed and added to the completed queue")


def pullComplete(top):
    global workComplete, otherManager
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
    global workComplete
    result = []
    for i in range(top):
        if not workComplete.empty():
            result.append(workComplete.get())
        else:
            break
    return result


@app.route('/enqueue', methods=['PUT'])
def enqueue():
    iterations = int(request.args.get('iterations'))
    data = request.get_data(as_text=True)
    enqueueWork(data, iterations)
    return 'Work enqueued successfully'


@app.route('/pullCompleted', methods=['POST'])
def pull_completed():
    top = int(request.args.get('top'))
    results = pullComplete(top)
    return jsonify(results)


@app.route('/internal/pullCompleteInternal', methods=['GET'])
def pull_complete_internal():
    top = int(request.args.get('top'))
    results = pullCompleteInternal(top)
    return jsonify(results)


@app.route('/internal/giveMeWork', methods=['GET'])
def give_me_work():
    work_item = giveMeWork()
    if work_item:
        return jsonify(work_item), 200
    else:
        return jsonify({'message': 'No available work'}), 404


@app.route('/internal/sendCompletedWork', methods=['POST'])
def send_completed_work():
    result = request.get_json()
    completed(result)
    return 'Completed work added successfully'


@app.route('/addSibling', methods=['POST'])
def add_sibling():
    global otherManager
    otherManager = request.args.get('manager')
    return 'Sibling added successfully'


@app.route('/internal/TryGetNodeQuota', methods=['GET'])
def try_get_node_quota():
    global numOfWorkers, maxNumOfWorkers
    if numOfWorkers < maxNumOfWorkers:
        maxNumOfWorkers -= 1
        return True
    return False


@app.route('/startPeriodicCheckThread', methods=['GET'])
def start_periodic_check_thread():
    worker_thread = threading.Thread(target=periodic_check)
    worker_thread.start()

    return "Worker Thread Started"


def periodic_check():
    while True:
        check_if_need_more_workers()
        time.sleep(5)


app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
