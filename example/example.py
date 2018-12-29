# -*- coding: utf-8 -*-

import logging
import os

from smapy import API
from smapy.logging import logging_setup
from smapy.utils import setenv, read_conf

LOGGER = logging.getLogger(__name__)


def get_app(api_conf):
    conf = read_conf(api_conf)
    setenv(conf['environ'])

    logging_setup(conf.get('logging'))

    LOGGER.info("Initializing the API")

    return API(conf)
