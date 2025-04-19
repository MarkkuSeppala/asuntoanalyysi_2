#!/bin/bash
# Start script for running app with gunicorn

# Install gunicorn if not already installed
pip install gunicorn

# Start gunicorn using the python module approach
export PYTHONPATH=$PYTHONPATH:$(pwd)
python -m gunicorn app:app 