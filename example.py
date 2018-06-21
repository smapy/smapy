#!/usr/bin/env python3.4
import logging
import logging.config
import os

from smapy.logging import SessionFilter
from smapy.utils import setenv, read_conf


def get_logging_config(logging_conf):
    dict_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': logging_conf['format']
            }
        },
        'filters': {
            'session_none': {
                '()': SessionFilter
            }
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'filters': ['session_none']
            },
            # 'rotating_file': {
            #     'level': logging_conf['level'],
            #     'class': 'cloghandler.ConcurrentRotatingFileHandler',
            #     'formatter': 'default',
            #     'filters': ['session_none'],
            #     'filename': os.path.join(logging_conf['logdir'], 'api.log'),
            #     'maxBytes': 100 * 1024 * 1024,    # 100Mb
            #     'backupCount': 5,
            # }
        },
        'loggers': {
            'requests': {
                'handlers': [logging_conf['handler']],
                'propagate': True,
                'level': 'WARN',
            },
            'urllib3': {
                'handlers': [logging_conf['handler']],
                'propagate': True,
                'level': 'WARN',
            },
            '': {
                'handlers': [logging_conf['handler']],
                'propagate': True,
                'level': logging_conf['level'],
            },
        }
    }
    return dict_config


def backdoor(bind, api):
    from gevent.backdoor import BackdoorServer

    print("Debugging backdoor listening at {}".format(bind))

    host, port = tuple(bind.split(':'))
    server = BackdoorServer((host, int(port)),
                            banner="API backdoor",
                            locals={'api': api})
    server.serve_forever()


def get_app(api_conf):
    conf = read_conf(api_conf)
    setenv(conf['environ'])

    logging.config.dictConfig(get_logging_config(conf['logging']))

    logging.getLogger().info("Initializing the API")

    # Import actions and resources here to make sure that the
    # environment is already configured
    from smapy import API, actions, resources
    api = API(conf)

    api.load_actions(actions.modules)

    # Misc
    api.add_resource("/multi_process", resources.misc.MultiProcess)
    api.add_resource('/report', resources.misc.Report)

    # Testing
    api.add_resource('/hello_world', resources.misc.HelloWorld)

    backdoor_bind = os.getenv('BACKDOOR')
    if backdoor_bind:
        backdoor(backdoor_bind, api)

    return api


if __name__ == '__main__':
    app = get_app('api/api.ini')
