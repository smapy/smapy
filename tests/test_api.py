# -*- coding: utf-8 -*-

import traceback
from importlib import reload
from unittest import TestCase
from unittest.mock import Mock, call, patch

import falcon

from smapy import api, middleware
from smapy.actions import hello


class TestExceptionSerializer(TestCase):

    def test_exception_serializer(self):
        """Just verify that to_dict is called and result assigned to body"""
        resp = Mock()
        exception = Mock()
        exception.to_dict.return_value = {'an': 'exception'}
        api.exception_serializer(None, resp, exception)

        self.assertEqual({'an': 'exception'}, resp.body)


class TestUnknownExceptionSerializer(TestCase):

    def test_unknown_exception_serializer_httperror(self):
        """If exception is an HTTPError raise it without doing anything else."""

        original = None
        with self.assertRaises(falcon.HTTPError) as raised:
            try:
                # We need to actually raise it to have a valid context.
                raise falcon.HTTPError(404)

            except falcon.HTTPError as ex:
                original = ex
                api.unknown_exception_serializer(ex, None, None, None)

        self.assertEqual(original, raised.exception)

    def test_unknown_exception_serializer_other(self):
        """If exception is NOT an HTTPError raise an HTTPInternalServerError."""

        tb = None
        with self.assertRaises(falcon.HTTPInternalServerError) as raised:
            try:
                # We need to actually raise it to have a valid context.
                raise Exception('a message')

            except Exception as ex:
                tb = traceback.format_exc().splitlines()[-3:]
                api.unknown_exception_serializer(ex, None, None, None)

        exception = raised.exception
        self.assertEqual('Exception: a message', exception.title)
        self.assertEqual(tb, exception.description)


class TestAPI(TestCase):

    def setUp(self):
        # Reload the api module to get rid of previous mocking
        reload(api)

    # #########################
    # _is_action(obj, module) #
    # #########################
    def test__is_action_not_a_class(self):
        """If object is not a class, it is not an Action."""
        obj = 'not a class'
        module = None

        is_action = api.API._is_action(obj, module)
        self.assertFalse(is_action)

    def test__is_action_imported(self):
        """If object was imported, it is not an Action."""
        # We use an imported module
        obj = api.MongoClient    # This is imported from pymongo inside api/__init__.py
        module = api

        is_action = api.API._is_action(obj, module)
        self.assertFalse(is_action)

    def test__is_action_not_an_action(self):
        """Obj is not a BaseAction subclass."""
        obj = api.API    # This is truly defined inside api/__init__.py, but it's not an Action
        module = api

        is_action = api.API._is_action(obj, module)
        self.assertFalse(is_action)

    def test__is_action_true(self):
        """Obj is really a BaseAction subclass."""
        obj = hello.World
        module = hello

        is_action = api.API._is_action(obj, module)
        self.assertTrue(is_action)

    # ###############################
    # _add_runnable(self, runnable) #
    # ###############################
    def test__add_runnable_duplicated(self):
        """If runnable is already registered, raise an exception."""

        # Override __init__
        api.API.__init__ = lambda x: None

        api_ = api.API()

        api_.runnables = {'a_runnable': Mock()}

        runnable = Mock()
        runnable.name = 'a_runnable'

        with self.assertRaises(ValueError) as ve:
            api_._add_runnable(runnable)

        exception = ve.exception
        self.assertEqual('Duplicated runnable name: a_runnable', str(exception))

    def test__add_runnable_ok(self):
        """If runnable is NOT registered, set it into runnables."""

        # Override __init__
        api.API.__init__ = lambda x: None

        api_ = api.API()

        api_.runnables = dict()

        runnable = Mock()
        runnable.name = 'a_runnable'

        api_._add_runnable(runnable)

        self.assertEqual({'a_runnable': runnable}, api_.runnables)

    # #############################
    # load_actions(self, modules) #
    # #############################
    # FIXME
    # @patch('smapy.api.find_submodules')
    # def test_load_actions(self, find_submodules_mock):
    #     """If a module attribute is an action, add it."""

    #     # Set up
    #     module = Mock()
    #     action = Mock()
    #     module.an_action = action

    #     find_submodules_mock.return_value = [module]

    #     # Override __init__
    #     api.API.__init__ = lambda x: None
    #     api_ = api.API()

    #     # Mock _is_action and _add_runnable
    #     def _is_action(obj, module):
    #         return obj == action

    #     api_._is_action = Mock(side_effect=_is_action)
    #     api_._add_runnable = Mock()

    #     # Actual call
    #     api_.load_actions('a.package')

    #     # Asserts
    #     find_submodules_mock.assert_called_once_with('a.package')
    #     api_._add_runnable.assert_called_once_with(action)

    # #####################################################
    # add_resource(self, route, resource_class, **kwargs) #
    # #####################################################
    def test_add_resource(self):
        """The resource must be initialized, added as a runnable and related to a route."""

        # Set up
        resource = Mock()
        api_ = Mock()
        api_.add_resource = api.API.add_resource.__get__(api_, api.API)

        # Actual call
        api_.add_resource('a_route', resource, keyword='argument')

        # Asserts
        api_._add_runnable.assert_called_once_with(resource, route='a_route', keyword='argument')
        api_.add_route.assert_called_once_with('a_route', resource)

    # #############################
    # _set_mongodb_up(self, conf) #
    # #############################
    @patch('smapy.api.MongoClient')
    def test__set_mongodb_up_no_audit(self, mongo_client_mock):
        """If audit is not defined, reuse self.mongodb."""

        # Set up
        mongo_client_mock.return_value = {
            'a_database': 'a_database',
            'audit_db': 'audit_db'    # this won't be used here
        }
        conf = {
            'mongodb': {
                'host': 'a_host',
                'port': 1234,
                'database': 'a_database'
            }
        }

        # Override __init__
        api.API.__init__ = lambda x: None
        api_ = api.API()

        # Actual call
        api_._set_mongodb_up(conf)

        # Asserts
        mongo_client_mock.assert_called_once_with(host='a_host', port=1234, connect=False)

        self.assertEqual('a_database', api_.mongodb)
        self.assertEqual('a_database', api_.auditdb)

    @patch('smapy.api.MongoClient')
    def test__set_mongodb_up_audit(self, mongo_client_mock):
        """If audit is defined, create a new client."""

        # Set up
        mongo_client_mock.return_value = {
            'a_database': 'a_database',
            'audit_db': 'audit_db'    # this WILL be used here
        }
        conf = {
            'mongodb': {
                'host': 'a_host',
                'port': 1234,
                'database': 'a_database'
            },
            'audit': {
                'host': 'audit_host',
                'port': 4321,
                'database': 'audit_db'
            }
        }

        # Override __init__
        api.API.__init__ = lambda x: None
        api_ = api.API()

        # Actual call
        api_._set_mongodb_up(conf)

        # Asserts
        calls = [
            call(host='a_host', port=1234, connect=False),
            call(host='audit_host', port=4321, connect=False)
        ]
        # self.assertEqual(calls, mongo_client_mock.call_args_list)
        assert calls == mongo_client_mock.call_args_list

        self.assertEqual('a_database', api_.mongodb)
        self.assertEqual('audit_db', api_.auditdb)

    # ######################
    # __init__(self, conf) #
    # ######################
    @patch('smapy.api.RemoteRunnable')
    def test___init__(self, remote_runnable_mock):
        """Make sure that everything is called with the right parameters."""

        # Set up
        conf = {
            'mongodb': 'mongodb',
            'audit': 'auditdb',
            'api': {
                'endpoint': 'an_endpoint',
                'default_resources': False
            }
        }

        # Mock _get_mongodb and _add_runnable
        def _get_mongodb(conf):
            return conf

        api.API._get_mongodb = Mock(side_effect=_get_mongodb)
        api.API.add_route = Mock()

        # Actual call
        api_ = api.API(conf)

        # Asserts
        _get_mongodb_calls = [
            call('mongodb'),
            call('auditdb')
        ]
        self.assertEqual(_get_mongodb_calls, api_._get_mongodb.call_args_list)

        # This is a bit hacky.
        # Here we go into the API._middleware list and look for the classes
        # which the registered methods belong to.
        self.assertEqual(2, len(api_._middleware[0]))
        self.assertIsInstance(api_._middleware[0][0][0].__self__, middleware.JSONSerializer)
        self.assertIsInstance(api_._middleware[0][1][0].__self__, middleware.ResponseBuilder)

        exception_serializer = api_._serialize_error
        self.assertEqual(api.exception_serializer, exception_serializer)

        unknown_exception_serializer = {e: f for e, f in api_._error_handlers}[Exception]
        self.assertEqual(
            api.unknown_exception_serializer.__name__,
            unknown_exception_serializer.__name__
        )

        self.assertEqual(api_.endpoint, 'an_endpoint')

        remote_runnable_mock.init.assert_called_once_with(api_)
        api_.add_route.assert_called_once_with(remote_runnable_mock.route, remote_runnable_mock)

        runnables = {
            'hello.World': hello.World
        }
        self.assertEqual(runnables, api_.runnables)
