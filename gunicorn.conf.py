import multiprocessing
import os

port = int(os.environ.get("PORT", 8000))  # Default to 8000 if not specified by Heroku
bind = f"0.0.0.0:{port}"   # Bind to the Heroku-assigned port
workers = multiprocessing.cpu_count() * 2 + 1  # Set the number of worker processes 
worker_class = "uvicorn.workers.UvicornWorker"  # Use Uvicorn as the worker class
timeout = 60