#!/bin/bash

# Run setup_manager.sh for the first time
echo "Running setup_manager.sh - First Run"
source ./setup_manager.sh
IP1="$PUBLIC_IP"
echo "IP1:$IP1"

## Run setup_manager.sh for the second time
echo "Running setup_manager.sh - Second Run"
source ./setup_manager.sh
IP2="$PUBLIC_IP"
echo "IP2:$IP2"

# Add siblings to each manager
  #curl -X POST "http://${IP1}:5000/addSibling?manager=${IP1}:5000"
# TODO: Uncomment this \/
curl -X POST "http://${IP1}:5000/addSibling?manager=${IP2}:5000"
curl -X POST "http://${IP2}:5000/addSibling?manager=${IP1}:5000"
#
#
## Start worker scan Thread
curl -X GET "http://${IP1}:5000/startPeriodicCheckThread"
curl -X GET "http://${IP2}:5000/startPeriodicCheckThread"

echo "###Both instances are live###"
echo "IP1:$IP1"
echo "IP2:$IP2"
