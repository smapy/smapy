# -*- coding: utf-8 -*-

import logging

from concurrent_log_handler import ConcurrentRotatingFileHandler


class SessionFilter(logging.Filter):
    """This is a filter which injects contextual information into the log."""

    def __init__(self, session=None, *args, **kwargs):
        super(SessionFilter, self).__init__(*args, **kwargs)
        self.session = session

    def filter(self, record):
        if not hasattr(record, 'session'):
            record.session = self.session

        return True


def logging_setup(conf):
    logger = logging.getLogger()
    logger.propagate = False

    default = '%(asctime)s - %(process)d - %(levelname)s - %(session)s - %(module)s - %(message)s'
    log_format = conf.get('format', default)
    formatter = logging.Formatter(log_format)

    log_level = conf.get('level', 'INFO')
    logger.setLevel(log_level)

    logfile = conf.get('logfile')
    if logfile:
        logsize = conf.get('logsize', 512 * 1024)
        retain = conf.get('logretain', 5)
        handler = ConcurrentRotatingFileHandler(logfile, 'a', logsize, retain)
    else:
        handler = logging.StreamHandler()

    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    logger.addHandler(handler)

    logger.addFilter(SessionFilter())
    handler.addFilter(SessionFilter())

    logging.getLogger('requests').setLevel('WARN')
    logging.getLogger('urllib3').setLevel('WARN')
