# -*- coding: utf-8 -*-

import logging
import os

from smapy.logging import SessionFilter
from smapy.utils import setenv, read_conf


def get_logging_config(logging_conf):
    return {
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

    return api
