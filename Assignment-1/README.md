# Exercise 1 - Parking Lot

### The scenario:  
A cloud-based system to manage a parking lot.
Actions:
Entry (record time, license plate and parking lot)
Exit (return the charge for the time in the parking lot)
Price – 10$ per hour (by 15 minutes)

### Endpoints:  
This code implements two HTTP endpoints:  
**POST** `/entry?plate=123-123-123&parkingLot=382` (Returns ticket id)  
**POST** `/exit?ticketId=1234` 
(Returns the license plate, total parked time, the parking lot id and the charge (based on 15 minutes increments).)  
The charge for parking is 10$ per hour.

### Implementation:
This project consists of 2 main files:  
* app.py - a simple Flask app implementing a simple web server answering both endpoints.
* setup.sh - bash script that utilizing the aws api to create and deploy the web server to the cloud.

### Prerequisites:
This project assumes you have aws configured:  
`# setup AWS CLI`  
`sudo apt install awscli zip`  
`# Configure AWS setup (keys, region, etc)`  
`aws configure`  
additionally, ensure you have jq installed. 

### To Run This Code:
Run `./setup.sh`  in the root of the project (Assignment-1)
The IP endpoints will be printed with
`"########Parking lot management app is now available at http://<PUBLIC_IP>:5000########"`
