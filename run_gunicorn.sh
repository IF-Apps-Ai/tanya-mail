#!/bin/bash
# Run Tanya Ma'il API with Gunicorn + UvicornWorker

# Activate venv
source venv/bin/activate

# Create logs directory if not exists
mkdir -p logs

# Run Gunicorn
exec gunicorn api:app -c gunicorn_config.py
