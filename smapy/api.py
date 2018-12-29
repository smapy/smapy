# -*- coding: utf-8 -*-

import importlib
import logging
import traceback

import falcon
from pymongo import MongoClient

from smapy import resources
from smapy.action import BaseAction
from smapy.middleware import JSONSerializer, ResponseBuilder
from smapy.runnable import RemoteRunnable
from smapy.utils import find_submodules

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


def import_object(object_name):
    """Import an object from its Fully Qualified Name."""
    package, name = object_name.rsplit('.', 1)
    return getattr(importlib.import_module(package), name)


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

    def import_runnable(self, runnable):
        actions_prefix = self.conf['api'].get('actions_prefix')
        if actions_prefix:
            runnable = actions_prefix + '.' + runnable

        return import_object(runnable)

        # package, name = runnable.rsplit('.', 1)
        # return getattr(importlib.import_module(package), name, None)

    def _add_runnable(self, runnable, **kwargs):
        if runnable.name in self.runnables:
            raise ValueError("Duplicated runnable name: {}".format(runnable.name))

        LOGGER.info("Adding new runnable %s", runnable.name)
        runnable.init(self, **kwargs)
        self.runnables[runnable.name] = runnable

    def get_runnable(self, runnable):
        runnable_class = self.runnables.get(runnable)
        if not runnable_class:
            runnable_class = self.import_runnable(runnable)
            self._add_runnable(runnable_class)

        if not runnable_class:
            raise falcon.HTTPInternalServerError('Invalid Runnable: {}'.format(runnable))

        return runnable_class

    def _load_actions(self, module):
        for attr in dir(module):
            obj = getattr(module, attr)
            if self._is_action(obj, module):
                self._add_runnable(obj)

    def load_actions(self, module):
        if isinstance(module, str):
            module = importlib.import_module(module)

        self._load_actions(module)
        for submodule in find_submodules(module):
            self.load_actions(submodule)

    def add_resource(self, route, resource_class, **kwargs):
        self._add_runnable(resource_class, route=route, **kwargs)
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

    def _load_default_resources(self, prefix=''):
        self.add_resource(prefix + '/multi_process', resources.misc.MultiProcess)
        self.add_resource(prefix + '/report', resources.misc.Report)
        self.add_resource(prefix + '/hello_world', resources.misc.HelloWorld)

    def _load_resources(self, conf):
        for resource_name, route in conf.items():
            resource = import_object(resource_name)
            self.add_resource(route, resource)

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
        if conf['api'].get('default_actions', True):
            self.load_actions('smapy.actions')

        actions_module = conf['api'].get('actions_module')
        if actions_module:
            self.load_actions(actions_module)

        if conf['api'].get('default_resources', True):
            prefix = conf['api'].get('default_resources_prefix', '')
            self._load_default_resources(prefix)

        resources = conf.get('resources')
        if resources:
            self._load_resources(conf.get('resources', dict()))
