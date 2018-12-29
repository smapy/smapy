# -*- coding: utf-8 -*-

from unittest import TestCase
from unittest.mock import Mock, call, patch

import falcon
from bson import ObjectId

from smapy.resource import BaseResource


class TestBaseResource(TestCase):

    def setUp(self):
        self.api = Mock(endpoint='http://host:port')

    # #######################
    # init(cls, api, rouce) #
    # #######################
    def test_init(self):
        """After calling the init method the class should have some attributes."""

        class TestResource(BaseResource):

            name = 'test_resource'

            def process(self, message):
                pass

        api = Mock()
        api.endpoint = 'http://an_endpoint'
        route = '/a_route'
        TestResource.init(api, route)

        # validate the attribute values of the class
        self.assertEqual(api, TestResource.api)
        self.assertEqual(route, TestResource.route)
        self.assertEqual(api.mongodb, TestResource.mongodb)
        self.assertEqual(api.conf, TestResource.conf)
        self.assertEqual('http://an_endpoint/a_route', TestResource.endpoint)
        self.assertEqual('test_resource', TestResource.logger.name)

    # #########################
    # run_local(cls, message) #
    # #########################
    def test_run_no_response_field(self):
        """If no response_field is defined, process response should be returned intact."""

        class TestResource(BaseResource):

            def process(self, message):
                return {'a': 'response'}

        api = Mock()
        api.endpoint = 'http://an_endpoint'
        TestResource.init(api, 'a_route')

        session = ObjectId('57b599f8ab1785652bb879a7')
        a_request = Mock(context={'session': session})
        test_resource = TestResource(a_request)

        response = test_resource.run_local({'a': 'message'})
        self.assertEqual({'a': 'response'}, response)

    def test_run_response_field_dict_response(self):
        """If response_field is defined, it should be extracted from process response."""

        class TestResource(BaseResource):

            response_field = 'a'

            def process(self, message):
                return {'a': 'response'}

        api = Mock()
        api.endpoint = 'http://an_endpoint'
        TestResource.init(api, 'a_route')

        session = ObjectId('57b599f8ab1785652bb879a7')
        a_request = Mock(context={'session': session})
        test_resource = TestResource(a_request)

        response = test_resource.run_local({})
        self.assertEqual('response', response)

    def test_run_response_field_no_response(self):
        """If response_field exists but response is None, it should be extracted from message."""

        class TestResource(BaseResource):

            response_field = 'a'

            def process(self, message):
                message['a'] = 'response'

        api = Mock()
        api.endpoint = 'http://an_endpoint'
        TestResource.init(api, 'a_route')

        session = ObjectId('57b599f8ab1785652bb879a7')
        a_request = Mock(context={'session': session})
        test_resource = TestResource(a_request)

        response = test_resource.run_local({})
        self.assertEqual('response', response)

    # ################################
    # on_get(cls, request, response) #
    # ################################
    # def test_on_get(self):
    #    """On get, run_local must be call with request.params"""
    #    FIXME: This should be adapted to the new run_public method

    #    class TestResource(BaseResource):

    #        def process(self, message):
    #            return message

    #    session = ObjectId('57b599f8ab1785652bb879a7')
    #    request = Mock(params={'some': 'params'}, context={'session': session})
    #    response = Mock()
    #    TestResource.on_get(request, response)

    #    self.assertEqual({'some': 'params'}, response.body)

    # ################################
    # on_post(cls, request, response) #
    # ################################
    # def test_on_post(self):
    #    """On post, run_local must be call with request.body"""
    #    FIXME: This should be adapted to the new run_public method

    #    class TestResource(BaseResource):

    #        def process(self, message):
    #            return message

    #    session = ObjectId('57b599f8ab1785652bb879a7')
    #    request = Mock(body={'some': 'params'}, context={'session': session})
    #    response = Mock()
    #    TestResource.on_post(request, response)

    #    self.assertEqual({'some': 'params'}, response.body)

    # ###############################
    # _get_runnable(self, runnable) #
    # ###############################
    def test__get_runnable_success(self):
        """If runnable exists, return a new instance."""

        resource = Mock()
        resource._get_runnable = BaseResource._get_runnable.__get__(resource, BaseResource)

        resource._get_runnable('a_runnable')
        resource.api.get_runnable.assert_called_once_with('a_runnable')
        resource.api.get_runnable.return_value.assert_called_once_with(resource.request)

    # ####################
    # _is_many(messages) #
    # ####################
    def test__is_many_generator(self):
        """If it's a generator, it is many."""
        a_generator = (a for a in [])
        is_many = BaseResource._is_many(a_generator)
        self.assertTrue(is_many)

    def test__is_many_not_a_list(self):
        """If it's neither a generator nor a list, it is not many."""
        is_many = BaseResource._is_many(dict())
        self.assertFalse(is_many)

    def test__is_only_one(self):
        """If it's a list but it has only one element, it is not many."""
        is_many = BaseResource._is_many([1])
        self.assertFalse(is_many)

    def test__is_long_list(self):
        """If it's a list with more than one element, it is many."""
        is_many = BaseResource._is_many([1, 2])
        self.assertTrue(is_many)

    # #########################################################
    # _run_one(self, runnable, messages, concurrency, remote) #
    # #########################################################
    @patch('smapy.resource.Pool')
    @patch('smapy.resource.gevent')
    def test__run_one_many(self, gevent_mock, pool_class_mock):
        """If multiple messages call runnable._run multiple times using gevent."""

        # Set up
        class OneResource(BaseResource):

            def process(self, message):
                pass

        class OtherResource(BaseResource):

            def process(self, message):
                pass

        api = Mock()
        api.endpoint = 'http://an_endpoint'
        OneResource.init(api, 'one_route')
        OtherResource.init(api, 'other_route')

        session = ObjectId('57b599f8ab1785652bb879a7')
        a_request = Mock(context={'session': session})
        one_resource = OneResource(a_request)
        other_resource = OtherResource(a_request)

        one_resource._get_runnable = Mock(return_value=other_resource)
        other_resource.run = Mock()

        pool_mock = Mock()
        pool_mock.spawn.side_effect = ['g1', 'g2', 'g3']
        pool_class_mock.return_value = pool_mock

        # Actual call
        messages = [{'message': 1}, {'message': 2}, {'message': 3}]
        one_resource._run_one('other_resource', messages, 3, False)

        # Asserts
        expected_calls = [call('other_resource')] * 3
        self.assertEqual(expected_calls, one_resource._get_runnable.call_args_list)

        pool_class_mock.assert_called_once_with(3)

        expected_calls = [
            call(other_resource.run, {'message': 1}, False, None),
            call(other_resource.run, {'message': 2}, False, None),
            call(other_resource.run, {'message': 3}, False, None),
        ]
        self.assertEqual(expected_calls, pool_mock.spawn.call_args_list)

        gevent_mock.wait.assert_called_once_with(['g1', 'g2', 'g3'])

        # run method thas NOT been called directly
        self.assertEqual(0, other_resource.run.call_count)

    def test__run_one_single(self):
        """If message is not a list just pass it to the runnable._run method once."""

        # Set up
        class OneResource(BaseResource):

            def process(self, message):
                pass

        class OtherResource(BaseResource):

            def process(self, message):
                pass

        api = Mock()
        api.endpoint = 'http://an_endpoint'
        OneResource.init(api, 'one_route')
        OtherResource.init(api, 'other_route')

        session = ObjectId('57b599f8ab1785652bb879a7')
        a_request = Mock(context={'session': session})
        one_resource = OneResource(a_request)
        other_resource = OtherResource(a_request)

        one_resource._get_runnable = Mock(return_value=other_resource)
        other_resource.run = Mock()

        # Actual call
        one_resource._run_one('other_resource', {}, 1, False)

        # Asserts
        one_resource._get_runnable.assert_called_once_with('other_resource')
        other_resource.run.assert_called_once_with({}, False, None)

    def test__run_one_single_list(self):
        """If message is a list with only one element, consider it a single message."""

        # Set up
        class OneResource(BaseResource):

            def process(self, message):
                pass

        class OtherResource(BaseResource):

            def process(self, message):
                pass

        api = Mock()
        api.endpoint = 'http://an_endpoint'
        OneResource.init(api, 'one_route')
        OtherResource.init(api, 'other_route')

        session = ObjectId('57b599f8ab1785652bb879a7')
        a_request = Mock(context={'session': session})
        one_resource = OneResource(a_request)
        other_resource = OtherResource(a_request)

        one_resource._get_runnable = Mock(return_value=other_resource)
        other_resource.run = Mock()

        # Actual call
        one_resource._run_one('other_resource', [{}], 1, False)

        # Asserts
        one_resource._get_runnable.assert_called_once_with('other_resource')
        other_resource.run.assert_called_once_with({}, False, None)

    # ###########################################################
    # _run_many(self, runnables, messages, concurrency, remote) #
    # ###########################################################
    def test__run_many_messages_list_different_length(self):
        """If messages is a list, its length must be the same as runnables."""

        # Set up
        class OneResource(BaseResource):

            def process(self, message):
                pass

        api = Mock()
        api.endpoint = 'http://an_endpoint'
        OneResource.init(api, 'one_route')

        session = ObjectId('57b599f8ab1785652bb879a7')
        a_request = Mock(context={'session': session})
        one_resource = OneResource(a_request)

        runnables = ['runnable_1', 'runnable_2', 'runnable_3']
        messages = [{'message': 1}, {'message': 3}]

        # Actual call
        with self.assertRaises(falcon.HTTPInternalServerError) as ex:
            one_resource._run_many(messages, runnables, 1, False)

        # Asserts
        exception = ex.exception

        self.assertEqual('Invalid Arguments', exception.title)
        self.assertEqual('messages and runnables lists should have the same length',
                         exception.description)

    @patch('smapy.resource.Pool')
    @patch('smapy.resource.gevent')
    def test__run_many_single_message(self, gevent_mock, pool_class_mock):
        """If messages is not a list, it must be converted into one."""

        # Set up
        class OneResource(BaseResource):
            def process(self, message):

                pass

        class OtherResource(BaseResource):

            def process(self, message):
                pass

        api = Mock()
        api.endpoint = 'http://an_endpoint'
        OneResource.init(api, 'one_route')

        session = ObjectId('57b599f8ab1785652bb879a7')
        a_request = Mock(context={'session': session})
        one_resource = OneResource(a_request)

        pool_mock = Mock()
        pool_mock.spawn.side_effect = ['g1', 'g2', 'g3']
        pool_class_mock.return_value = pool_mock

        # Actual call
        runnables = ['runnable_1', 'runnable_2', 'runnable_3']
        messages = {'a': 'message'}
        one_resource._run_many(runnables, messages, 3, False)

        # Asserts
        pool_class_mock.assert_called_once_with(3)

        expected_calls = [
            call(one_resource._run_one, 'runnable_1', {'a': 'message'}, 1, False),
            call(one_resource._run_one, 'runnable_2', {'a': 'message'}, 1, False),
            call(one_resource._run_one, 'runnable_3', {'a': 'message'}, 1, False),
        ]
        self.assertEqual(expected_calls, pool_mock.spawn.call_args_list)

        gevent_mock.wait.assert_called_once_with(['g1', 'g2', 'g3'])

    # #################################################################
    # invoke(self, runnable, message, concurrency=None, remote=False) #
    # #################################################################
    def test_invoke_runnable_list(self):
        """If runnable is a list call _run_many."""

        # Set up
        class OneResource(BaseResource):

            def process(self, message):
                pass

        api = Mock()
        api.endpoint = 'http://an_endpoint'
        OneResource.init(api, 'one_route')

        session = ObjectId('57b599f8ab1785652bb879a7')
        a_request = Mock(context={'session': session})
        one_resource = OneResource(a_request)

        one_resource._run_many = Mock()
        one_resource._run_one = Mock()

        # Actual call
        runnable = ['runnable_1', 'runnable_2', 'runnable_3']
        message = [{'message': 1}, {'message': 2}]
        one_resource.invoke(runnable, message, 1, True)

        # Asserts
        one_resource._run_many.assert_called_once_with(runnable, message, 1, True)
        self.assertEqual(0, one_resource._run_one.call_count)

    def test_invoke_single_runnable(self):
        """If runnable is not a list call _run_one."""

        # Set up
        class OneResource(BaseResource):

            def process(self, message):
                pass

        api = Mock()
        api.endpoint = 'http://an_endpoint'
        OneResource.init(api, 'one_route')

        session = ObjectId('57b599f8ab1785652bb879a7')
        a_request = Mock(context={'session': session})
        one_resource = OneResource(a_request)

        one_resource._run_many = Mock()
        one_resource._run_one = Mock()

        # Actual call
        runnable = 'a_runnable'
        message = [{'message': 1}, {'message': 2}]
        one_resource.invoke(runnable, message, 1, True)

        # Asserts
        self.assertEqual(0, one_resource._run_many.call_count)
        one_resource._run_one.assert_called_once_with(runnable, message, 1, True, None)
