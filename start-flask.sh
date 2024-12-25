#!/bin/bash

cd "$(dirname "$0")"
source ./venv/bin/activate
flask run --host=0.0.0.0 --port=5002
