import copy
import datetime
import json
from unittest import TestCase
from unittest.mock import MagicMock, patch

import falcon
from bson import ObjectId

from smapy.runnable import RemoteRunnable, Runnable, RunnableMeta


class TestRunnableMeta(TestCase):

    def test_default_name(self):
        """If the class has no name defined, it should be set to __module__.__name__."""

        class Base(metaclass=RunnableMeta):
            pass

        class Test(Base):
            pass

        self.assertEqual(Test.name, 'test_runnable.Test')

    def test_custom_name(self):

        class Base(metaclass=RunnableMeta):
            pass

        class Test(Base):
            name = 'custom'

        self.assertEqual(Test.name, 'custom')


class TestRemoteRunnable(TestCase):

    def setUp(self):
        self.api = MagicMock(endpoint='http://host:port')

    # ################
    # init(cls, api) #
    # ################
    def test_init(self):
        """After calling the init method the class should have some attributes."""

        api = MagicMock()
        api.endpoint = 'http://an_endpoint'
        RemoteRunnable.init(api)

        # validate the attribute values of the class
        self.assertEqual(api, RemoteRunnable.api)
        self.assertEqual(api.mongodb, RemoteRunnable.mongodb)
        self.assertEqual('http://an_endpoint/_remote', RemoteRunnable.endpoint)
        self.assertEqual(RemoteRunnable.__name__, RemoteRunnable.name)
        self.assertEqual(RemoteRunnable.name, RemoteRunnable.logger.name)

    # ##########################
    # __init__(self, runnable) #
    # ##########################
    def test___init__(self):
        """After calling the __init__ method some attributes should have changed."""

        api = MagicMock()
        api.endpoint = 'http://an_endpoint'
        RemoteRunnable.init(api)

        a_runnable = MagicMock()
        a_runnable.name = 'a_runnable'
        remote_runnable = RemoteRunnable(a_runnable)

        # validate the attribute values of the class
        self.assertEqual(api, RemoteRunnable.api)
        self.assertEqual(api.mongodb, RemoteRunnable.mongodb)
        self.assertEqual('http://an_endpoint/_remote', RemoteRunnable.endpoint)
        self.assertEqual(RemoteRunnable.__name__, RemoteRunnable.name)
        self.assertEqual(RemoteRunnable.name, RemoteRunnable.logger.name)

        # validate the attribute values of the instance
        self.assertEqual(a_runnable, remote_runnable.runnable)
        self.assertEqual('RemoteRunnable(a_runnable)', remote_runnable.name)
        self.assertEqual('RemoteRunnable(a_runnable)', remote_runnable.logger.logger.name)

    # ####################
    # run(self, message) #
    # ####################
    @patch('smapy.runnable.requests')
    def test_run_success(self, requests_mock):
        """Message should be POSTed and updated with the response."""
        now = datetime.datetime(2000, 1, 1)
        message = {
            'a_string': 'a string',
            'a_datetime': now
        }

        # Set the requests_mock up:
        #    - requests.post returns a response object.
        #    - the response object has status_code=200 and
        #      has a method json which returns a dictionary
        json_text = json.dumps({
            'results': {
                'message': {
                    'a_new_string': 'a new string',
                    'a_string': 'a modified string',
                    'a_datetime': {
                        '$date': 946684800000
                    },
                }
            },
            'status': falcon.HTTP_OK
        })
        response_mock = MagicMock(status_code=200, text=json_text)
        post_mock = MagicMock(return_value=response_mock)
        session_mock = MagicMock()
        session_mock.post = post_mock
        requests_mock.Session.return_value = session_mock

        # create the RemoteRunnable instance and call its run method.
        session = ObjectId('57b599f8ab1785652bb879a7')
        a_runnable = MagicMock(session=session)
        a_runnable.name = 'a_runnable'

        RemoteRunnable.init(self.api)
        remote_runnable = RemoteRunnable(a_runnable)
        remote_runnable.run(message)

        # make the validations
        expected_data = {
            "message": {
                "a_datetime": {
                    "$date": 946684800000
                },
                "a_string": "a string"
            },
            "runnable": "a_runnable"
        }
        expected_endpoint = self.api.endpoint + RemoteRunnable.route

        self.assertEqual(post_mock.call_count, 1)

        call_args = post_mock.call_args[0]
        self.assertEqual(len(call_args), 1)
        call_endpoint = call_args[0]
        self.assertEqual(expected_endpoint, call_endpoint)

        call_kwargs = post_mock.call_args[1]
        self.assertEqual(len(call_kwargs), 2)

        self.assertTrue('headers' in call_kwargs)
        expected_headers = {'API-SESSION': '57b599f8ab1785652bb879a7'}
        self.assertEqual(expected_headers, call_kwargs['headers'])

        self.assertTrue('data' in call_kwargs)
        call_data = call_kwargs['data']

        # We need to load the JSON into a dict, otherwise we could have differences due to sorting
        call_data_dict = json.loads(call_data)
        self.assertEqual(expected_data, call_data_dict)

    @patch('smapy.runnable.requests')
    def test_run_wrong_response_not_ok(self, requests_mock):
        """If remote response is not 200 OK and InternalServerError must be raised."""

        # Set the requests_mock up:
        #    - requests.post returns a response object.
        #    - the response object has status_code=500 and
        #      has a method json which raises a ValueError
        json_text = json.dumps({
            'status': falcon.HTTP_INTERNAL_SERVER_ERROR
        })
        response_mock = MagicMock(status_code=500, text=json_text)
        post_mock = MagicMock(return_value=response_mock)
        session_mock = MagicMock()
        session_mock.post = post_mock
        requests_mock.Session.return_value = session_mock

        # create the RemoteRunnable instance and call its run method.
        session = ObjectId('57b599f8ab1785652bb879a7')
        a_runnable = MagicMock(session=session)
        a_runnable.name = 'a_runnable'

        RemoteRunnable.init(self.api)
        remote_runnable = RemoteRunnable(a_runnable)

        with self.assertRaises(falcon.HTTPInternalServerError) as ex:
            remote_runnable.run({})

        # make the validations
        exception = ex.exception
        self.assertEqual('RemoteRunnable(a_runnable)', exception.title)
        self.assertEqual('Error status: 500 Internal Server Error', exception.description)

    @patch('smapy.runnable.requests')
    def test_run_wrong_response_format(self, requests_mock):
        """If remote response is not a JSON an InternalServerError must be rised."""

        # Set the requests_mock up:
        #    - requests.post returns a response object.
        #    - the response object has status_code=500 and
        #      the text is not a valid json
        response_mock = MagicMock(status_code=500, text='This is not a valid JSON')
        post_mock = MagicMock(return_value=response_mock)
        session_mock = MagicMock()
        session_mock.post = post_mock
        requests_mock.Session.return_value = session_mock

        # create the RemoteRunnable instance and call its run method.
        session = ObjectId('57b599f8ab1785652bb879a7')
        a_runnable = MagicMock(session=session)
        a_runnable.name = 'a_runnable'

        RemoteRunnable.init(self.api)
        remote_runnable = RemoteRunnable(a_runnable)

        with self.assertRaises(falcon.HTTPInternalServerError) as ex:
            remote_runnable.run({})

        # make the validations
        exception = ex.exception
        self.assertEqual('RemoteRunnable(a_runnable)', exception.title)
        self.assertEqual('Invalid remote response format', exception.description)

    # #########################
    # on_post(cls, req, resp) #
    # #########################
    def test_on_post_success(self):
        """If must run the runnable.run_local method and return the modified message."""

        # Set mocks up
        def run_local_side_effect(message):
            # Store a copy of the received message
            self.run_local_message = copy.deepcopy(message)
            message['a'] = 'value'

        run_local_mock = MagicMock(side_effect=run_local_side_effect)
        runnable_mock = MagicMock(run_local=run_local_mock)
        runnable_class_mock = MagicMock(return_value=runnable_mock)
        self.api.runnables = {
            'a_runnable': runnable_class_mock
        }

        # Actual call
        now = datetime.datetime(2000, 1, 1)
        message = {
            'a_string': 'a string',
            'a_datetime': now
        }
        body = {
            'message': message,
            'runnable': 'a_runnable'
        }
        req = MagicMock(body=body)
        req.headers = {'API-SESSION': '57b599f8ab1785652bb879a7'}
        resp = MagicMock()

        RemoteRunnable.init(self.api)
        RemoteRunnable.on_post(req, resp)

        # Asserts
        # The runnable instance has been created
        runnable_class_mock.assert_called_once_with(req)

        # runnable.run_local has been called once, with the right message
        self.assertEqual(1, run_local_mock.call_count)
        expected_run_local_message = {
            'a_string': 'a string',
            'a_datetime': now
        }
        self.assertEqual(expected_run_local_message, self.run_local_message)

        # The modified message has been set into the response
        expected_body = {
            'message': {
                'a_string': 'a string',
                'a_datetime': now,
                'a': 'value'
            },
            'runnable': 'a_runnable'
        }
        self.assertEqual(expected_body, resp.body)

    def test_on_post_missing_param(self):
        """If a param is missing it raises an exception."""

        # Actual call
        body = {
            'runnable': 'a_runnable'
        }
        req = MagicMock(body=body)
        resp = MagicMock()

        RemoteRunnable.init(self.api)

        with self.assertRaises(falcon.HTTPMissingParam) as ex:
            RemoteRunnable.on_post(req, resp)

        # Asserts
        exception = ex.exception
        self.assertEqual(exception.title, 'Missing parameter')
        self.assertEqual(exception.description, 'The "message" parameter is required.')


class TestRunnable(TestCase):

    def test_init(self):

        class TestRunnable(Runnable):
            def run_local(self, message):
                pass

        api = MagicMock()
        TestRunnable.init(api)

        request = MagicMock()
        test_runnable = TestRunnable(request)

        # validate the attribute values of the class
        self.assertEqual(api, TestRunnable.api)
        self.assertEqual(api.mongodb, TestRunnable.mongodb)
        self.assertEqual(api.conf, TestRunnable.conf)
        self.assertEqual(TestRunnable.name, TestRunnable.logger.name)

        # validate the attribute values of the instance
        self.assertEqual(api, test_runnable.api)
        self.assertEqual(api.mongodb, test_runnable.mongodb)
        self.assertEqual(api.conf, test_runnable.conf)
        self.assertEqual(test_runnable.name, test_runnable.logger.logger.name)

    @patch('smapy.runnable.RemoteRunnable')
    def test_run_local(self, remote_runnable_class_mock):
        """If remote=False, RemoteRunnable must NOT be used."""

        # Set up
        class TestRunnable(Runnable):
            def run_local(self, message):
                pass

        session = ObjectId('57b599f8ab1785652bb879a7')
        a_request = MagicMock()
        a_request.context = {'session': session}

        api = MagicMock()
        api.endpoint = 'http://an_endpoint'
        TestRunnable.init(api)

        test_runnable = TestRunnable(a_request)
        test_runnable.run_local = MagicMock()

        # Actual call
        message = {}
        test_runnable.run(message)

        # Asserts
        self.assertEqual(0, remote_runnable_class_mock.call_count)
        test_runnable.run_local.assert_called_once_with(message)

    @patch('smapy.runnable.RemoteRunnable')
    def test_run_remote(self, remote_runnable_class_mock):
        """If remote=True, RemoteRunnable must be used."""

        # Set up
        class TestRunnable(Runnable):
            def run_local(self, message):
                pass

        session = ObjectId('57b599f8ab1785652bb879a7')
        a_request = MagicMock()
        a_request.context = {'session': session}

        api = MagicMock()
        api.endpoint = 'http://an_endpoint'
        TestRunnable.init(api)

        test_runnable = TestRunnable(a_request)
        test_runnable.run_local = MagicMock()

        remote_runnable_mock = MagicMock()
        remote_runnable_class_mock.return_value = remote_runnable_mock

        # Actual call
        message = {}
        test_runnable.run(message, remote=True)

        # Asserts
        remote_runnable_class_mock.assert_called_once_with(test_runnable)
        remote_runnable_mock.run.assert_called_once_with(message)

        self.assertEqual(0, test_runnable.run_local.call_count)
