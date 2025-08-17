import multiprocessing
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get port from environment or default to 8000
PORT = os.getenv("PORT", "8000")
bind = f"0.0.0.0:{PORT}"

workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
loglevel = "info"
accesslog = "logs/gunicorn-access.log"
errorlog = "logs/gunicorn-error.log"
max_requests = 1000
max_requests_jitter = 50
timeout = 60
graceful_timeout = 30
keepalive = 2
proc_name = "tanya-mail-api"
