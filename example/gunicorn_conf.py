# import os
import multiprocessing as mp

bind = "127.0.0.1:8001"
workers = (2 * mp.cpu_count()) + 1
timeout = 3600
worker_class = "gevent"

# logs_dir = "logs"
# errorlog = os.path.join(logs_dir, "gunicorn.log")
# accesslog = os.path.join(logs_dir, "access.log")
loglevel = "info"

raw_env = [
    # This allows us to pass some default environment variables to the app
    # "LOGS_DIR={}".format(logs_dir),
    "BIND={}".format(bind),
]
