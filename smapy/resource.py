# -*- coding: utf-8 -*-

import datetime
import os
import socket
import traceback
import types
from abc import abstractmethod

import falcon
import gevent
from gevent.pool import Pool

from smapy.runnable import Runnable
from smapy.utils import get_bool, get_ms


class BaseResource(Runnable):
    """
    TODO:
        - implement session tracking
        - implement exception tracking
        - implement generic input processing and validation
    """

    response_field = None    # Only return this field in the response
    sync = None    # If True, make this resource always synchronous
    audit = True   # If False, skip session creation and audit tracking for this resource

    @classmethod
    def init(cls, api, route):
        super(BaseResource, cls).init(api)
        cls.route = route
        cls.endpoint = api.endpoint + route

    # ###########################
    # ### main resource flow ####
    # ###########################

    @abstractmethod
    def process(self, message):
        """The actual resource code should be implemented here by subclasses."""

    @classmethod
    def _is_sync(cls, request):
        if 'sync' in request.params:
            return get_bool(request.params, 'sync')

        elif cls.sync is not None:
            return cls.sync

        return cls.conf['api'].get('sync', False)

    @classmethod
    def start_session(cls, request, sync):
        session = {
            'status': 'RUNNING',
            'alive': True,
            'sync': sync,
            'resource': cls.name,
            'in_ts': request.context['in_ts'],
            'body': request.body,
            'params': request.params,
            'pid': os.getpid(),
            'host': socket.gethostname(),
            'env': {k: v for k, v in request.env.items() if '.' not in k}
        }
        request.context['session'] = cls.mongodb.session.insert(session)
        request.context['internal'] = False
        request.context['sync'] = sync
        cls.logger.info("Starting new session %s.", session['_id'])
        return sync

    def end_session(self, response, status='OK'):
        in_ts = self.context['in_ts']
        out_ts = datetime.datetime.utcnow()
        self.context['out_ts'] = out_ts
        elapsed = get_ms(out_ts - in_ts)
        self.context['elapsed'] = elapsed

        if not self.context['internal']:
            match = {
                '_id': self.session
            }
            elapsed = get_ms(out_ts - in_ts)
            update = {
                '$set': {
                    'out_ts': out_ts,
                    'elapsed': elapsed,
                    'response': response,
                    'status': status,
                    'alive': False,
                }
            }
            self.mongodb.session.update_one(match, update)

        self.logger.info("Ending session %s. Status: %s, Elapsed: %sms",
                         self.session, status, elapsed)

    def run_local(self, message):
        response = self.process(message) or message
        if response and self.response_field:
            response = response.get(self.response_field)

        return response

    def _run_public(self, body):
        status = 'OK'
        try:
            response = self.run_local(body)

        except BaseException as ex:
            self.logger.exception("Caught an uncontrolled Exception")
            status = 'EXCEPTION'
            exception = "{}: {}".format(ex.__class__.__name__, ex),
            tb = traceback.format_exc().splitlines()[-3:]
            response = {
                'status': status,
                'exception': exception,
                'traceback': tb
            }
            raise falcon.HTTPInternalServerError("Uncontrolled Exception", tb)

        finally:
            if self.audit:
                self.end_session(response, status)

        return response

    @classmethod
    def run_public(cls, request, body):
        sync = cls._is_sync(request)
        request.context['sync'] = sync
        request.context['audit'] = cls.audit

        if cls.audit:
            sync = cls.start_session(request, sync)

        resource = cls(request)
        if sync:
            return resource._run_public(body)

        else:
            gevent.spawn(resource._run_public, body)

    @classmethod
    def on_get(cls, request, response):
        response.body = cls.run_public(request, request.params)

    @classmethod
    def on_post(cls, request, response):
        response.body = cls.run_public(request, request.body)

    # ##########################
    # ### running runnables ####
    # ##########################

    def _get_runnable(self, runnable):
        runnable_class = self.api.runnables.get(runnable)
        if not runnable_class:
            raise falcon.HTTPInternalServerError(
                'Invalid Runnable',
                'Runnable {} not found in registry'.format(runnable)
            )

        return runnable_class(self.request)

    @staticmethod
    def _is_many(messages):
        if isinstance(messages, types.GeneratorType):
            return True

        elif not isinstance(messages, list):
            return False

        else:
            return len(messages) > 1

    def _run_one(self, runnable, messages, concurrency, remote, callback=None):
        """Run a single runnable on a single or many messages."""

        if self._is_many(messages):
            if concurrency == 1:
                # Skip gevent usage
                for message in messages:
                    runnable_ = self._get_runnable(runnable)
                    runnable_.run(message, remote, callback)

            else:
                # run the same runnable on many messages concurrently
                pool = Pool(concurrency)
                greenlets = []

                for message in messages:
                    runnable_ = self._get_runnable(runnable)
                    greenlet = pool.spawn(runnable_.run, message, remote, callback)
                    greenlets.append(greenlet)

                gevent.wait(greenlets)

        else:
            # messages is actually a single message, so skip the gevent part
            if isinstance(messages, list):
                message = messages[0]

            else:
                message = messages

            runnable_ = self._get_runnable(runnable)
            runnable_.run(message, remote, callback)

    def _run_many(self, runnables, messages, concurrency, remote):
        """Run many runnables on a single or many messages."""

        if isinstance(messages, list):
            # each message corresponds to a single runnable, so we validate the list lengths
            if len(messages) != len(runnables):
                raise falcon.HTTPInternalServerError(
                    'Invalid Arguments',
                    'messages and runnables lists should have the same length'
                )

        else:
            # We convert the message into a list of messages, to make
            # the next block of code behave in a uniform way
            messages = [messages] * len(runnables)

        pool = Pool(concurrency)
        greenlets = []

        for runnable, message in zip(runnables, messages):
            greenlet = pool.spawn(self._run_one, runnable, message, 1, remote)
            greenlets.append(greenlet)

        gevent.wait(greenlets)

    def invoke(self, runnable, message=None, concurrency=None, remote=False, callback=None):
        concurrency = int(concurrency) if concurrency else self.conf['api'].get('concurrency', 10)

        if isinstance(runnable, list):
            if callback:
                raise NotImplementedError("Callback functions work only on single runnables")

            self._run_many(runnable, message, concurrency, remote)

        else:
            self._run_one(runnable, message, concurrency, remote, callback)
