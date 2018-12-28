# -*- coding: utf-8 -*-

import logging


class SessionFilter(logging.Filter):
    """This is a filter which injects contextual information into the log."""

    def __init__(self, session=None, *args, **kwargs):
        super(SessionFilter, self).__init__(*args, **kwargs)
        self.session = session

    def filter(self, record):
        if not hasattr(record, 'session'):
            record.session = self.session

        return True
