import base64
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
        time.sleep(5)
    # TODO: Uncomment this \/
    # subprocess.call(["sudo", "shutdown", "now"])


def DoWork(work):
    logging.info(f"Worker processing work")
    buffer = work[0]
    iterations = work[1]
    logging.info(f"buffer = {work[0]}")
    logging.info(f"iterations = {work[1]}")

    output = hashlib.sha512(buffer).digest()

    logging.info(f"Worker completed iteration 1")
    for i in range(iterations - 1):
        output = hashlib.sha512(output).digest()
        logging.info(f"Worker completed iteration {i+2}")

    return output


def give_me_work(manager):
    url = f"http://{manager}/internal/giveMeWork"
    try:
        logging.info(f"give_me_work {url}")
        response = requests.get(url)
        if response.status_code == 200:
            encoded_work_item = response.text  # Get the encoded work item as a string
            work_item_str = base64.b64decode(encoded_work_item).decode('utf-8')  # Decode the base64 and convert to string
            work_item = eval(work_item_str)  # Convert the string back to a list or tuple
            logging.info(f"Received work from {manager}")
            return work_item
        else:
            logging.error(f"Failed to retrieve work from {manager}. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred while querying {manager}: {e}")
    logging.info(f"No work from {manager}")
    return None


def send_completed_work(manager, result):
    logging.info(f"Sending completed work ({result}) to {manager}")
    url = f"http://{manager}/internal/sendCompletedWork"

    encoded_result = base64.b64encode(str(result).encode('utf-8')).decode('utf-8')

    response = requests.post(url, json=encoded_result)
    if response.status_code == 200:
        logging.info(f"Completed work sent successfully to {manager}")
    else:
        logging.error(f"Failed to send completed work to {manager}. Status code: {response.status_code}")


# my_ip = os.environ.get('MY_IP')
# sibling_ip = os.environ.get('OTHER_IP')
#
# managers = [my_ip, sibling_ip]
# perform_work(managers)

my_ip = os.environ.get('MY_IP')

managers = [my_ip]
perform_work(managers)
