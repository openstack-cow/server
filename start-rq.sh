#!/bin/bash

cd "$(dirname "$0")"
source ./venv/bin/activate
rq worker --with-scheduler
