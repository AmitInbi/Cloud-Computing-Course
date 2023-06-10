from flask import Flask
from threading import Thread
import time
import sys
import requests
import hashlib


app = Flask(__name__)


class Worker:
    def DoWork(self, work):
        buffer = work[0]
        iterations = work[1]
        output = hashlib.sha512(buffer).digest()
        for i in range(iterations - 1):
            output = hashlib.sha512(output).digest()
        return output

    def loop(self):
        nodes = [sys.argv[1], sys.argv[2]]
        startTime = time.time()

        while time.time() - startTime <= 300:
            for i in range(len(nodes)):
                work = self.giveMeWork(nodes[i])
                if work is not None:
                    result = self.DoWork(work)
                    self.completed(nodes[i], result)
                    continue
            time.sleep(0.1)

        # Notify the parent that the Worker is done
        # You can replace this line with appropriate logic
        print("WorkerDone")

    def giveMeWork(self, node):
        url = f"http://{node}/giveMeWork"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to retrieve work from {node}")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while querying {node}: {e}")
        return None

    def completed(self, node, result):
        url = f"http://{node}/sendCompletedWork"
        response = requests.post(url, json=result)
        if response.status_code == 200:
            print('Completed work sent successfully')
        else:
            print('Failed to send completed work')


worker = Worker()


@app.route('/startWorker', methods=['POST'])
def start_worker():
    thread = Thread(target=worker.loop)
    thread.start()
    return 'Worker started', 200


if __name__ == '__main__':
    app.run()
