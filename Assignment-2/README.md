# Exercise 2 - Dynamic workload

### The scenario:  
This system creates 2 "manager"'s EC2 instances that given work, raise "worker" EC2 instances.
The worker instances have the IP's of both managers, and they query them for available work items.
The work consists of binary data sent in the body of the enqueue request.

### Endpoints:  
This code implements two HTTP endpoints:  
**PUT** `/enqueue?iterations=2` 
(with body containing a binary file)  
**POST** `/pullCompleted?top=1` 
(Gets the top most recent completed work _from either manager_!)  

### Implementation:
This project consists of 6 main files:  
* **setup.sh** - bash script that utilizing the aws api to create and deploy both managers and trigger them to begin work.
* **setup_manager.sh** - bash script that creates a manager instance (triggered twice by ./setup.sh)
* **setup_worker.sh** - bash script that creates a worker instance (triggered by work in manager's workQueue)
* **manager_endpoints.py** - a Flask app implementing the endpoints. 
  Additionaly, has a thread checking for available work in queue for over a specified amount of time, triggering setup_worker.sh if necessary.
* **worker.py** - queries both managers for available work items and performs number of 'iterations' SHA512 computations, dies if no work available for 5 minutes.
* **binary_file.bin** - 256kb of random binary data to be sent in the body of an enqueue request to be hashed.
  

### Prerequisites:
This project assumes you have aws configured:  
`# setup AWS CLI`  
`sudo apt install awscli zip`  
`# Configure AWS setup (keys, region, etc)`  
`aws configure`  
additionally, ensure you have jq installed. 

### To Run This Code:
Run `./setup.sh`  in the root of the project (Assignment-2)
The IP endpoints will be printed with  
`echo "###Both instances are live###"`  
`echo "IP1:$IP1"`  
`echo "IP2:$IP2"`  