# -*- coding: utf-8 -*-

import logging
import os
import sys

from gunicorn.app.base import BaseApplication

from smapy.logging_utils import logging_setup
from smapy.utils import setenv, read_conf


class SmapyApplication(BaseApplication):

    @staticmethod
    def _load_config(config_file):
        config = read_conf(config_file)
        setenv(config['environ'])

        # Force some values
        api_config = config['api']
        api_config['worker_class'] = 'gevent'
        api_config.setdefault('bind', '127.0.0.1:8001')
        if not api_config.get('endpoint'):
            api_config['endpoint'] = 'http://' + api_config['bind']

        return config

    def __init__(self, config_file):
        self.config = self._load_config(config_file)
        super().__init__("%(prog)s CONFIG_FILE")

    def load_config(self):
        for key, value in self.config['api'].items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key, value)

    def load(self):
        from smapy.api import API

        logging_setup(self.config.get('logging'))
        logging.getLogger(__name__).info("Initializing the API")

        return API(self.config)


if __name__ == '__main__':
    config_file = sys.argv[1]
    SmapyApplication(config_file).run()
