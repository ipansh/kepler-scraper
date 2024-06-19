import multiprocessing

bind = "0.0.0.0:$PORT"         # Bind to the port assigned by Heroku
workers = multiprocessing.cpu_count() * 2 + 1  # Set the number of worker processes 
worker_class = "uvicorn.workers.UvicornWorker"  # Use Uvicorn as the worker class
timeout = 60