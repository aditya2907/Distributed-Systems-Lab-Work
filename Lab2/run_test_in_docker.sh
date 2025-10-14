#!/bin/bash

# Run Python test from a Python container on the same Docker network

SCRIPT_NAME=$1

if [ -z "$SCRIPT_NAME" ]; then
    echo "Usage: ./run_test_in_docker.sh <script_name>"
    echo "Example: ./run_test_in_docker.sh write_concern_test.py"
    exit 1
fi

# Run Python container on the same network and execute the script
docker run --rm -it \
    --network lab2_mongo-net \
    -v "$(pwd)":/workspace \
    -w /workspace \
    python:3.11-slim \
    bash -c "pip install --quiet pymongo && python3 $SCRIPT_NAME"
