from datetime import datetime, timedelta
import time
import requests
import hashlib
import subprocess
import os
import logging

# Configure logging
logging.basicConfig(filename='worker.log', level=logging.INFO)


def perform_work(managers):
    last_completion_time = datetime.now()

    while datetime.now() - last_completion_time <= timedelta(seconds=300):
        for manager in managers:
            logging.info(f"Scanning for work from: {manager}")
            work = give_me_work(manager)
            if work is not None:
                logging.info(f"Found work from: {manager}")
                result = DoWork(work)
                send_completed_work(manager, result)
                last_completion_time = datetime.now()
                continue
            else:
                logging.info(f"Not found work from: {manager}")
        time.sleep(1)
    # TODO: Uncomment this \/
    # subprocess.call(["sudo", "shutdown", "now"])


def DoWork(work):
    buffer = work[0]
    iterations = work[1]
    output = hashlib.sha512(buffer).digest()
    for i in range(iterations - 1):
        output = hashlib.sha512(output).digest()
    return output

    logging.info("Worker completed the work.")


def give_me_work(manager):
    url = f"http://{manager}/internal/giveMeWork"
    try:
        logging.info(f"give_me_work {url}")
        response = requests.get(url)
        if response.status_code == 200:
            work = response.json()
            logging.info(f"Received work from {manager}: {work}")
            return work
        else:
            logging.error(f"Failed to retrieve work from {manager}. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred while querying {manager}: {e}")
    logging.info(f"No work from {manager}")
    return None


def send_completed_work(node, result):
    url = f"http://{node}/internal/sendCompletedWork"
    response = requests.post(url, json=result)
    if response.status_code == 200:
        logging.info(f"Completed work sent successfully to {node}")
    else:
        logging.error(f"Failed to send completed work to {node}. Status code: {response.status_code}")


# my_ip = os.environ.get('MY_IP')
# sibling_ip = os.environ.get('OTHER_IP')
#
# managers = [my_ip, sibling_ip]
# perform_work(managers)

my_ip = os.environ.get('MY_IP')

managers = [my_ip]
perform_work(managers)
