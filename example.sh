#!/bin/bash

echo "WARNING: This script is intended to be used only during development!"
echo "Usage: ./api_devel.sh [-s port] [num of workers (default=1)]"

if [ "$1" == "-s" ]; then
    shift
    PORT=$1
    shift

    echo "Starting mock sentiment API"
    cd api/mocks
    gunicorn sentiment:app -k gevent -w 1 -b 0.0.0.0:$PORT &
    cd ../..
fi

WORKERS=${1:-1}

# if [ "$WORKERS" == "1" ]; then
#     ENV="--env BACKDOOR=127.0.0.1:5001"
# fi

gunicorn "example:get_app('example.ini')" \
         -t 100000000 \
         --reload \
         -c api/gunicorn_conf.py \
         -w $WORKERS \
         $ENV \
         --log-level info
