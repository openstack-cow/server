#!/bin/bash

# Check and add nameserver 8.8.8.8 if not present
grep -q "^nameserver 8.8.8.8$" /etc/resolv.conf || echo "nameserver 8.8.8.8" | sudo tee -a /etc/resolv.conf > /dev/null

# Check and add nameserver 8.8.4.4 if not present
grep -q "^nameserver 8.8.4.4$" /etc/resolv.conf || echo "nameserver 8.8.4.4" | sudo tee -a /etc/resolv.conf > /dev/null

# Check and add hostname entry if not present
if ! grep -q "127.0.1.1[[:space:]]\+$1" /etc/hosts; then
    echo "127.0.1.1    $1" | sudo tee -a /etc/hosts > /dev/null
fi

sudo apt update
sudo apt install -y ca-certificates curl gnupg unzip zip htop nano

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# export a few variables to keep track of mysql and redis ports
export MYSQL_HOST_PORT=3310 # start from 3310
export REDIS_HOST_PORT=6390 # start from 6390
