import datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch

import falcon
from bson import ObjectId

from smapy.middleware import JSONSerializer, ResponseBuilder, SessionHandler


class TestJSONSerializer(TestCase):

    def test_process_request_no_content_length(self):
        """If content_lenght is not given req.body must be an empty dict."""

        # Set up
        req = MagicMock()
        req.content_length = None
        resp = MagicMock()

        # Actual call
        JSONSerializer().process_request(req, resp)

        # Asserts
        self.assertEqual(dict(), req.body)

    def test_process_request_content_length_is_0(self):
        """If content_lenght==0 is not given req.body must be an empty dict."""

        # Set up
        req = MagicMock()
        req.content_length = 0
        resp = MagicMock()

        # Actual call
        JSONSerializer().process_request(req, resp)

        # Asserts
        self.assertEqual(dict(), req.body)

    def test_process_request_no_body(self):
        """If body is empty an excpetion must be raised."""

        # Set up
        req = MagicMock()
        req.content_length = 100
        req.stream.read.return_value = None
        resp = MagicMock()

        # Actual call
        with self.assertRaises(falcon.HTTPBadRequest) as ex:
            JSONSerializer().process_request(req, resp)

        # Asserts
        exception = ex.exception
        self.assertEqual('Empty request body', exception.title)
        self.assertEqual('A valid JSON document is required.', exception.description)

    def test_process_request_encoding_error(self):
        """If body is not a encoded as UTF-8 an excpetion must be raised."""

        # Set up
        req = MagicMock()
        req.content_length = 100
        req.stream.read.return_value = 'this is not UTF-8'.encode('utf-16')
        resp = MagicMock()

        # Actual call
        with self.assertRaises(falcon.HTTPBadRequest) as ex:
            JSONSerializer().process_request(req, resp)

        # Asserts
        exception = ex.exception
        self.assertEqual('Encoding Error', exception.title)
        self.assertEqual('Request must be encoded as UTF-8.', exception.description)

    def test_process_request_malformed_json(self):
        """If body is not a valid JSON an excpetion must be raised."""

        # Set up
        req = MagicMock()
        req.content_length = 100
        req.stream.read.return_value = b'this is not a JSON'
        resp = MagicMock()

        # Actual call
        with self.assertRaises(falcon.HTTPBadRequest) as ex:
            JSONSerializer().process_request(req, resp)

        # Asserts
        exception = ex.exception
        self.assertEqual('Malformed JSON', exception.title)
        self.assertEqual('A valid JSON document is required.', exception.description)

    def test_process_request_success(self):
        """If body is a valid JSON it must be loaded into req.body."""

        # Set up
        req = MagicMock()
        req.content_length = 100
        req.stream.read.return_value = '{"valid": "JSON"}'.encode('utf-8')
        resp = MagicMock()

        # Actual call
        JSONSerializer().process_request(req, resp)

        # Asserts
        body = {
            'valid': 'JSON'
        }
        self.assertEqual(body, req.body)

    def test__serial_datetime(self):
        """If obj is a datetime, isoformat it."""

        obj = datetime.datetime(2000, 1, 1)

        # Actual call
        serialized = JSONSerializer._serial(obj)

        # Asserts
        self.assertEqual('2000-01-01T00:00:00', serialized)

    def test__serial_objectid(self):
        """If obj is an ObjectId, print it as a string."""

        obj = ObjectId('57bee205ab17852928644d3e')

        # Actual call
        serialized = JSONSerializer._serial(obj)

        # Asserts
        self.assertEqual('57bee205ab17852928644d3e', serialized)

    def test__serial_error(self):
        """If obj is not serializable, raise an exception."""

        obj = MagicMock()

        # Actual call
        with self.assertRaises(TypeError) as ex:
            JSONSerializer._serial(obj)

        # Asserts
        exception = ex.exception
        self.assertEqual('MagicMock is not JSON serializable', str(exception))

    def test_process_response_empty(self):
        """If body is empty do nothing."""

        # Set up
        req = MagicMock()
        resp = MagicMock()
        resp.body = None
        resource = MagicMock()

        # Actual call
        JSONSerializer().process_response(req, resp, resource)

        # Asserts
        self.assertIsNone(resp.body)

    def test_process_response_string(self):
        """If body is already string do nothing."""

        # Set up
        req = MagicMock()
        resp = MagicMock()
        resp.body = 'a string'
        resource = MagicMock()

        # Actual call
        JSONSerializer().process_response(req, resp, resource)

        # Asserts
        self.assertEqual('a string', resp.body)

    def test_process_response_internal(self):
        """If internal, serialize using json_util."""

        # Set up
        req = MagicMock()
        req.context = {'internal': True}
        resp = MagicMock()
        resp.body = {'a datetime': datetime.datetime(2000, 1, 1)}
        resource = MagicMock()

        # Actual call
        JSONSerializer().process_response(req, resp, resource)

        # Asserts
        expected_body = '{\n    "a datetime": {\n        "$date": 946684800000\n    }\n}'
        self.assertEqual(expected_body, resp.body)

    def test_process_response_external(self):
        """If not internal, serialize using the custom serializer."""

        # Set up
        req = MagicMock()
        req.context = {'internal': False}
        resp = MagicMock()
        resp.body = {'a datetime': datetime.datetime(2000, 1, 1)}
        resource = MagicMock()

        # Actual call
        JSONSerializer().process_response(req, resp, resource)

        # Asserts
        expected_body = '{\n    "a datetime": "2000-01-01T00:00:00"\n}'
        self.assertEqual(expected_body, resp.body)


class TestResponseBuilder(TestCase):

    @patch('smapy.middleware.os')
    @patch('smapy.middleware.socket')
    def test_process_response(self, socket_mock, os_mock):
        """Add a JSON layer with metadata about the server."""

        # Set up
        req = MagicMock()
        req.context = {
            'session': ObjectId('57bee205ab17852928644d3e'),
            'in_ts': datetime.datetime(2000, 1, 1),
            'out_ts': datetime.datetime(2000, 1, 1, 0, 0, 1),
            'elapsed': 1000
        }
        resp = MagicMock()
        resp.body = {'a response': 'body'}
        resp.status = 'OK'
        resource = MagicMock()

        os_mock.getpid.return_value = 1234
        socket_mock.gethostname.return_value = 'a hostname'

        # Actual call
        ResponseBuilder().process_response(req, resp, resource)

        # Asserts
        expected_body = {
            'status': 'OK',
            'pid': 1234,
            'host': 'a hostname',
            'in_ts': datetime.datetime(2000, 1, 1),
            'out_ts': datetime.datetime(2000, 1, 1, 0, 0, 1),
            'elapsed': 1000,
            'results': {
                'a response': 'body'
            },
            'session': ObjectId('57bee205ab17852928644d3e')
        }
        self.assertEqual(expected_body, resp.body)


class TestSessionHandler(TestCase):

    def test_process_request_internal(self):
        """If API-SESSION header exists, get the session_id from it."""

        # Set up
        req = MagicMock()
        req.headers = {'API-SESSION': '57bee205ab17852928644d3e'}
        req.context = dict()
        resp = MagicMock()

        mongodb = MagicMock()

        # Actual call
        SessionHandler(mongodb).process_request(req, resp)

        # Asserts
        self.assertEqual(ObjectId('57bee205ab17852928644d3e'), req.context['session'])
        self.assertTrue(req.context['internal'])

    @patch('smapy.middleware.os')
    @patch('smapy.middleware.socket')
    @patch('smapy.middleware.datetime')
    def test_process_request_external(self, datetime_mock, socket_mock, os_mock):
        """If API-SESSION header does not exist, create a new session."""

        # Set up
        req = MagicMock()
        req.headers = dict()
        req.context = dict()
        req.body = {'a': 'body'}
        req.params = {'some': 'params'}
        req.env = {
            'gevent.unwanted': 'we do not want this',
            'WANTED': 'we do want this'
        }
        resp = MagicMock()

        os_mock.getpid.return_value = 1234
        socket_mock.gethostname.return_value = 'a hostname'
        datetime_mock.datetime.utcnow.return_value = datetime.datetime(2000, 1, 1)

        mongodb = MagicMock()
        mongodb.session.insert.return_value = ObjectId('57bee205ab17852928644d3e')

        # Actual call
        SessionHandler(mongodb).process_request(req, resp)

        # Asserts
        self.assertEqual(ObjectId('57bee205ab17852928644d3e'), req.context['session'])
        self.assertFalse(req.context['internal'])
        self.assertEqual(datetime.datetime(2000, 1, 1), req.context['in_ts'])

        expected_session = {
            'in_ts': datetime.datetime(2000, 1, 1),
            'body': {'a': 'body'},
            'params': {'some': 'params'},
            'pid': 1234,
            'host': 'a hostname',
            'env': {'WANTED': 'we do want this'}
        }
        mongodb.session.insert.assert_called_once_with(expected_session)

    def test_process_response_internal(self):
        """If internal do nothing."""

        # Set up
        req = MagicMock()
        req.context = {
            'internal': True,
            'in_ts': datetime.datetime(2000, 1, 1),
            'out_ts': datetime.datetime(2000, 1, 1, 0, 0, 1),
            'elapsed': 1000
        }
        resp = MagicMock()
        resource = MagicMock()

        mongodb = MagicMock()

        # Actual call
        SessionHandler(mongodb).process_response(req, resp, resource)

        # Asserts
        self.assertEqual(0, mongodb.session.update_one.call_count)

    @patch('smapy.middleware.datetime')
    def test_process_response_external(self, datetime_mock):
        """If not internal, update the session."""

        # Set up
        req = MagicMock()
        req.context = {
            'in_ts': datetime.datetime(2000, 1, 1),
            'session': ObjectId('57bee205ab17852928644d3e'),
            'internal': False
        }
        resp = MagicMock()
        resp.body = {
            'a': 'body'
        }
        resource = MagicMock()

        datetime_mock.datetime.utcnow.return_value = datetime.datetime(2000, 1, 1, 0, 0, 1)

        mongodb = MagicMock()

        # Actual call
        SessionHandler(mongodb).process_response(req, resp, resource)

        # Asserts
        expected_match = {
            '_id': ObjectId('57bee205ab17852928644d3e')
        }
        expected_update = {
            '$set': {
                'out_ts': datetime.datetime(2000, 1, 1, 0, 0, 1),
                'elapsed': 1000,
                'response': {
                    'a': 'body'
                }
            }
        }
        mongodb.session.update_one.assert_called_once_with(expected_match, expected_update)
