#!/bin/bash

set -euo pipefail

# Create key pair to connect to instances and save locally
printf "Creating key pair...\n"
readonly KEY_NAME="cloud-course-assignment-1-$(date +'%N')"
readonly KEY_PEM="$KEY_NAME.pem"
printf "Key name: %s\n" "$KEY_NAME"
aws ec2 create-key-pair --key-name "$KEY_NAME" | jq -r ".KeyMaterial" > "$KEY_PEM"
chmod 400 "$KEY_PEM"

# Setup firewall
printf "Setting up firewall...\n"
readonly SEC_GRP="my-sg-$(date +'%N')"
printf "Security group name: %s\n" "$SEC_GRP"
aws ec2 create-security-group --group-name "$SEC_GRP" --description "Access my instances"

# Figure out my IP
readonly MY_IP="$(curl ipinfo.io/ip)"
printf "My IP: %s\n" "$MY_IP"

# Setup rule allowing SSH access to MY_IP only
printf "Setting up firewall rules...\n"
aws ec2 authorize-security-group-ingress --group-name "$SEC_GRP" --port 22 --protocol tcp --cidr "$MY_IP/32"
# #
# # Setup rule allowing HTTP (port 5000) access to MY_IP only
# aws ec2 authorize-security-group-ingress --group-name "$SEC_GRP" --port 5000 --protocol tcp --cidr "$MY_IP/32"

# Setup rule allowing HTTP (port 5000) access to all IPs
aws ec2 authorize-security-group-ingress --group-name "$SEC_GRP" --port 5000 --protocol tcp --cidr 0.0.0.0/0

# Set AMI ID and instance type
readonly UBUNTU_22_04_AMI="ami-007855ac798b5175e"
readonly INSTANCE_TYPE="t2.micro"

# Create Ubuntu 22.04 instance
printf "Creating Ubuntu 22.04 instance...\n"
readonly RUN_INSTANCES=$(aws ec2 run-instances --image-id "$UBUNTU_22_04_AMI" --instance-type "$INSTANCE_TYPE" --key-name "$KEY_NAME" --security-groups "$SEC_GRP")
readonly INSTANCE_ID=$(echo "$RUN_INSTANCES" | jq -r '.Instances[0].InstanceId')

# Wait for instance creation
printf "Waiting for instance creation...\n"
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"
readonly PUBLIC_IP=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" | jq -r '.Reservations[0].Instances[0].PublicIpAddress')
printf "New instance %s @ %s\n" "$INSTANCE_ID" "$PUBLIC_IP"

# Deploy code to production
printf "Deploying code to production...\n"
readonly APP_FILE="app.py"
scp -i $KEY_PEM -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=60" app.py ubuntu@$PUBLIC_IP:/home/ubuntu/


# SSH into the instance and run the necessary commands  to deploy the app
printf "########Running this command: ssh -T -i $KEY_PEM ubuntu@$PUBLIC_IP########\n"
echo "########running ssh command########\n"
ssh -T -i "$KEY_PEM" -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@"$PUBLIC_IP" << EOF
    sudo apt update 
    sudo apt install python3-pip -y
    sudo pip install Flask
    export FLASK_APP=$APP_FILE
    nohup flask run --host 0.0.0.0  &>/dev/null &
    exit
EOF

# Print out the URL where the app is running
printf "\n"
printf "##########################################\n"
printf "########Parking lot management app is now available at http://%s:5000########\n" "$PUBLIC_IP"
printf "##########################################\n"



