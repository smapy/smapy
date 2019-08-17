# -*- coding: utf-8 -*-

import datetime
import sys
import traceback
from abc import abstractmethod

from smapy import utils
from smapy.runnable import Runnable


class BaseAction(Runnable):

    audit = True    # If False, skip audit insert
    initial_message = None

    def copy_message(self, message):
        self.initial_message = dict()
        try:
            self.initial_message = utils.safecopy(message)

        except RuntimeError as rerror:
            self.logger.error('Could not copy initial message: %s', rerror)

    def insert_audit(self):
        self.start_ts = datetime.datetime.utcnow()

        audit = {
            'action': self.name,
            'session': self.session,
            'start_ts': self.start_ts,
            'status': 'RUNNING'
        }
        self.aid = self.auditdb.actions.insert(audit)

    def update_audit(self, message, exception):
        end_ts = datetime.datetime.utcnow()

        audit = {
            'end_ts': end_ts,
            'elapsed': utils.get_ms(end_ts - self.start_ts),
        }
        if exception:
            audit['status'] = 'EXCEPTION'
            audit['exception'] = exception
            audit['request'] = self.initial_message
            audit['message'] = message

        else:
            audit['status'] = 'OK'

        match = {'_id': self.aid}
        update = {'$set': audit}
        self.auditdb.actions.update(match, update)

    def run_local(self, message):
        if self.audit and self.context.get('audit', True):
            self.insert_audit()
            self.copy_message(message)

        exception = None
        try:
            self.process(message)

        except BaseException as e:
            self.logger.exception("Caught an uncontrolled Exception")
            exception = traceback.format_exception(*sys.exc_info())
            if not isinstance(e, Exception):
                raise

        finally:
            if self.audit and self.context.get('audit', True):
                self.update_audit(message, exception)

    @abstractmethod
    def process(self, message):
        """The actual action code should be implemented here by subclasses."""
