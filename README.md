[![PyPi][pypi-img]][pypi-url]
[![TravisCI][travis-img]][travis-url]
[![CodeCov][codecov-img]][codecov-url]

[travis-img]: https://travis-ci.org/csala/smapy.svg?branch=master
[travis-url]: https://travis-ci.org/csala/smapy
[pypi-img]: https://img.shields.io/pypi/v/smapy.svg
[pypi-url]: https://pypi.python.org/pypi/smapy
[codecov-img]: https://codecov.io/gh/csala/smapy/branch/master/graph/badge.svg
[codecov-url]: https://codecov.io/gh/csala/smapy

# Smapy

Simple Modular APIs written in Python.

- Free software: MIT license
- Documentation: https://csala.github.io/smapy

## Overview

**Smapy** is a framework built on top of [Falcon](https://falconframework.org) and
[gunicorn](https://gunicorn.org/), which allows building modular, distributed and
asynchronous-capable service oriented Web APIs writing as little Python code as possible.

## Installation

The simplest and recommended way to install **Smapy** is using `pip`:

```bash
pip install smapy
```

Alternatively, clone the repository and install it from source running the `make install` command.

```bash
git clone git@github.com:csala/smapy.git
cd smapy
make install
```

For development, you can use the `make install-develop` command instead in order to install all
the required dependencies for testing and code linting.

## Getting Started

All you need to start a **Smapy** application is to execute the `smapy` command line utility:

```bash
$ smapy
[2018-12-29 21:53:03 +0100] [25213] [INFO] Starting gunicorn 19.9.0
[2018-12-29 21:53:03 +0100] [25213] [INFO] Listening at: http://127.0.0.1:8001 (25213)
[2018-12-29 21:53:03 +0100] [25213] [INFO] Using worker: gevent
[2018-12-29 21:53:03 +0100] [25216] [INFO] Booting worker with pid: 25216
2018-12-29 21:53:03,304 - 25216 - INFO - None - application - Initializing the API
2018-12-29 21:53:03,307 - 25216 - INFO - None - api - Adding new runnable hello.World
2018-12-29 21:53:03,307 - 25216 - INFO - None - api - Adding new runnable misc.MultiProcess
2018-12-29 21:53:03,307 - 25216 - INFO - None - api - Adding new runnable misc.Report
2018-12-29 21:53:03,308 - 25216 - INFO - None - api - Adding new runnable misc.HelloWorld
```

After that, you can start playing with it through HTTP requests:

```
$ curl localhost:8001/hello
{
    "elapsed": 0.08,
    "host": "hostname",
    "in_ts": "2018-05-06T20:37:48.671867",
    "out_ts": "2018-05-06T20:37:48.671947",
    "pid": 31789,
    "results": null,
    "session": null,
    "status": "404 Not Found"
}

$ curl localhost:8001/hello_world
{
    "elapsed": 12.044,
    "host": "hostname",
    "in_ts": "2018-05-06T20:37:58.759039",
    "out_ts": "2018-05-06T20:37:58.771083",
    "pid": 31789,
    "results": null,
    "session": "5aef67a6ab17857c2d81a6ea",
    "status": "200 OK"
}

$ curl localhost:8001/hello_world?sync=True
{
    "elapsed": 26.668,
    "host": "hostname",
    "in_ts": "2018-05-06T20:38:03.903315",
    "out_ts": "2018-05-06T20:38:03.929983",
    "pid": 31789,
    "results": {
        "hello": "world!",
        "sync": "True"
    },
    "session": "5aef67abab17857c2d81a6ec",
    "status": "200 OK"
}

$ curl localhost:8001/report?session=5aef67a6ab17857c2d81a6ea
{
    "elapsed": 19.758,
    "host": "hostname",
    "in_ts": "2018-05-06T20:39:49.670267",
    "out_ts": "2018-05-06T20:39:49.690025",
    "pid": 31789,
    "results": {
        "actions": {
            "OK": 1
        },
        "last_activity": "2018-05-06T20:37:58.812000",
        "session": {
            "_id": "5aef67a6ab17857c2d81a6ea",
            "alive": false,
            "body": {},
            "elapsed": "0:00:00.058000",
            "env": {
                "HTTP_ACCEPT": "*/*",
                "HTTP_HOST": "localhost:8001",
                "HTTP_USER_AGENT": "curl/7.47.0",
                "PATH_INFO": "/hello_world",
                "QUERY_STRING": "",
                "RAW_URI": "/hello_world",
                "REMOTE_ADDR": "127.0.0.1",
                "REMOTE_PORT": "50636",
                "REQUEST_METHOD": "GET",
                "SCRIPT_NAME": "",
                "SERVER_NAME": "127.0.0.1",
                "SERVER_PORT": "8001",
                "SERVER_PROTOCOL": "HTTP/1.1",
                "SERVER_SOFTWARE": "gunicorn/19.8.1"
            },
            "host": "hostname",
            "in_ts": "2018-05-06T20:37:58.759000",
            "out_ts": "2018-05-06T20:37:58.817000",
            "params": {},
            "pid": 31789,
            "resource": "misc.HelloWorld",
            "response": {
                "hello": "world!"
            },
            "status": "OK",
            "sync": false
        },
        "session_data": {
            "links": 0,
            "occurrences": 0,
            "post": 0
        }
    },
    "session": "5aef6815ab17857c2d81a6ef",
    "status": "200 OK"
}
```
