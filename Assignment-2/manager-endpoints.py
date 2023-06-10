from flask import Flask, request, jsonify
from threading import Timer
from queue import Queue
from datetime import datetime, timedelta
import subprocess


app = Flask(__name__)


class EndpointNode:
    def __init__(self):
        self.workQueue = Queue()
        self.workComplete = []
        self.maxNumOfWorkers = 0
        self.numOfWorkers = 0
        self.timer = None

    def timer_10_sec(self):
        if not self.workQueue.empty():
            work_item = self.workQueue.queue[0]
            if datetime.now() - work_item[2] > timedelta(seconds=15):
                if self.numOfWorkers < self.maxNumOfWorkers:
                    self.spawnWorker()
                else:
                    if self.otherNode.TryGetNodeQuota():
                        self.maxNumOfWorkers += 1

        # Schedule the next execution of timer_10_sec
        self.timer = Timer(10, self.timer_10_sec)
        self.timer.start()

    def start_timer(self):
        # Start the timer initially
        self.timer = Timer(10, self.timer_10_sec)
        self.timer.start()

    def stop_timer(self):
        # Stop the timer
        if self.timer is not None:
            self.timer.cancel()

    def spawnWorker(self):
        try:
            subprocess.run(['bash', 'setup_worker.sh'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to spawn worker: {e}")

    def TryGetNodeQuota(self):
        if self.numOfWorkers < self.maxNumOfWorkers:
            self.maxNumOfWorkers -= 1
            return True
        return False

    def enqueueWork(self, data, iterations):
        self.workQueue.put((data, iterations, datetime.now()))

    def giveMeWork(self):
        return self.workQueue.get() or None

    def completed(self, result):
        self.workComplete.append(result)

    def pullComplete(self, n):
        results = self.workComplete[:n]
        if len(results) > 0:
            return results
        try:
            return self.otherNode.pullCompleteInternal(n)
        except:
            return []


endpoint_node = EndpointNode()


@app.route('/enqueue', methods=['PUT'])
def enqueue():
    iterations = int(request.args.get('iterations'))
    data = request.get_data(as_text=True)
    endpoint_node.enqueueWork(data, iterations)
    return 'Work enqueued successfully'


@app.route('/pullCompleted', methods=['POST'])
def pull_completed():
    top = int(request.args.get('top'))
    results = endpoint_node.pullComplete(top)
    return jsonify(results)


@app.route('/pullCompleteInternal', methods=['POST'])
def pull_complete_internal():
    n = request.json.get('n')
    results = endpoint_node.workComplete[:n]
    return jsonify(results)


@app.route('/giveMeWork', methods=['GET'])
def give_me_work():
    work_item = endpoint_node.giveMeWork()
    if work_item:
        return jsonify(work_item), 200
    else:
        return jsonify({'message': 'No available work'}), 404


@app.route('/sendCompletedWork', methods=['POST'])
def send_completed_work():
    # Get the completed work from the request
    data = request.get_json()
    result = data['result']
    endpoint_node.completed(result)
    return 'Completed work added successfully'


if __name__ == '__main__':
    endpoint_node.start_timer()
    app.run()
