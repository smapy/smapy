# -*- coding: utf-8 -*-

from  multiprocessing import cpu_count

bind = "127.0.0.1:8001"
workers = (2 * cpu_count()) + 1
timeout = 3600
worker_class = "gevent"

# errorlog = "gunicorn.log"
# accesslog = "access.log"
loglevel = "info"

raw_env = [
    # This allows us to pass some default environment variables to the app
    # "LOGS_DIR={}".format(logs_dir),
    "BIND={}".format(bind),
]
