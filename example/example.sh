#!/bin/bash

cd $(dirname $0)

WORKERS=${1:-1}

gunicorn "example:get_app('example.ini')" \
         -t 100000000 \
         --reload \
         -c gunicorn_conf.py \
         -w $WORKERS \
         $ENV \
         --log-level info
