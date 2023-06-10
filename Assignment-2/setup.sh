#!/bin/bash

# Run setup_manager.sh for the first time
echo "Running setup_manager.sh - First Run"
source ./setup_manager.sh
IP1="$PUBLIC_IP"

# Run setup_manager.sh for the second time
echo "Running setup_manager.sh - Second Run"
source ./setup_manager.sh
IP2="$PUBLIC_IP"

# Add siblings to each manager
curl -X POST "http://${IP1}/addSibling?manager=${IP2}"
curl -X POST "http://${IP2}/addSibling?manager=${IP1}"
