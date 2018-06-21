# -*- coding: utf-8 -*-

__author__ = 'Carles Sala Cladellas'
__email__ = 'carles@pythiac.com',
__version__ = '0.0.1'

import logging
import traceback

import falcon
from pymongo import MongoClient

from smapy.action import BaseAction
from smapy.middleware import JSONSerializer, ResponseBuilder
from smapy.runnable import RemoteRunnable

LOGGER = logging.getLogger(__name__)


class Request(falcon.Request):
    body = None


def exception_serializer(req, resp, exception):
    resp.body = exception.to_dict()


def unknown_exception_serializer(ex, req, resp, params):
    if isinstance(ex, falcon.HTTPError):
        raise ex

    LOGGER.exception("Uncontrolled Exception")
    raise falcon.HTTPInternalServerError(
        "{}: {}".format(ex.__class__.__name__, ex),
        traceback.format_exc().splitlines()[-3:]
    )


class API(falcon.API):

    @staticmethod
    def _is_action(obj, module):
        if not isinstance(obj, type):
            # Not a class
            return False

        elif obj.__module__ is not module.__name__:
            # obj was not defined within module, but rather imported
            return False

        else:
            return issubclass(obj, BaseAction)

    def _add_runnable(self, runnable):
        if runnable.name in self.runnables:
            raise ValueError("Duplicated runnable name: {}".format(runnable.name))

        self.runnables[runnable.name] = runnable

    def _load_action(self, module):
        for attr in dir(module):
            obj = getattr(module, attr)
            if self._is_action(obj, module):
                obj.init(self)
                self._add_runnable(obj)

    def load_actions(self, modules):
        for module in modules.values():
            self._load_action(module)

    def add_resource(self, route, resource_class, **kwargs):
        resource_class.init(self, route, **kwargs)
        self._add_runnable(resource_class)
        self.add_route(route, resource_class)

    def _get_mongodb(self, conf):
        host = conf['host']
        port = int(conf['port'])
        database = conf['database']

        client = MongoClient(host=host, port=port, connect=False)
        return client[database]

    def _set_mongodb_up(self, conf):
        mongo_conf = conf['mongodb']
        self.mongodb = self._get_mongodb(mongo_conf)

        audit_conf = conf.get('audit')
        if audit_conf:
            self.auditdb = self._get_mongodb(audit_conf)

        else:
            self.auditdb = self.mongodb

    def __init__(self, conf):
        self.conf = conf
        self._set_mongodb_up(conf)

        middleware = [
            JSONSerializer(),
            ResponseBuilder(),
        ]
        super(API, self).__init__(request_type=Request, middleware=middleware)

        self.set_error_serializer(exception_serializer)
        self.add_error_handler(Exception, unknown_exception_serializer)

        self.endpoint = conf['api']['endpoint']

        RemoteRunnable.init(self)
        self.add_route(RemoteRunnable.route, RemoteRunnable)

        self.runnables = dict()
