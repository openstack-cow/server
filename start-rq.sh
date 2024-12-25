#!/bin/bash

cd "$(dirname "$0")"
source ./venv/bin/activate
source ../demo-openrc
rq worker --with-scheduler
