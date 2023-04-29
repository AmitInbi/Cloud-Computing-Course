#!/bin/bash

set -euo pipefail

# Create key pair to connect to instances and save locally
readonly KEY_NAME="cloud-course-$(date +'%N')"
readonly KEY_PEM="$KEY_NAME.pem"
aws ec2 create-key-pair --key-name "$KEY_NAME" | jq -r ".KeyMaterial" > "$KEY_PEM"
chmod 400 "$KEY_PEM"

# Setup firewall
readonly SEC_GRP="my-sg-$(date +'%N')"
aws ec2 create-security-group --group-name "$SEC_GRP" --description "Access my instances"

# Figure out my IP
readonly MY_IP="$(curl ipinfo.io/ip)"
printf "My IP: %s\n" "$MY_IP"

## Setup rule allowing SSH access to MY_IP only
#aws ec2 authorize-security-group-ingress --group-name "$SEC_GRP" --port 22 --protocol tcp --cidr "$MY_IP/32"
#
## Setup rule allowing HTTP (port 5000) access to MY_IP only
#aws ec2 authorize-security-group-ingress --group-name "$SEC_GRP" --port 5000 --protocol tcp --cidr "$MY_IP/32"

# Set AMI ID and instance type
readonly UBUNTU_20_04_AMI="ami-042e8287309f5df03"
readonly INSTANCE_TYPE="t3.micro"

# Create Ubuntu 20.04 instance
printf "Creating Ubuntu 20.04 instance...\n"
readonly RUN_INSTANCES=$(aws ec2 run-instances --image-id "$UBUNTU_20_04_AMI" --instance-type "$INSTANCE_TYPE" --key-name "$KEY_NAME" --security-groups "$SEC_GRP")
readonly INSTANCE_ID=$(echo "$RUN_INSTANCES" | jq -r '.Instances[0].InstanceId')

# Wait for instance creation
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"
readonly PUBLIC_IP=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" | jq -r '.Reservations[0].Instances[0].PublicIpAddress')
printf "New instance %s @ %s\n" "$INSTANCE_ID" "$PUBLIC_IP"

# Deploy code to production
readonly APP_FILE="app.py"
