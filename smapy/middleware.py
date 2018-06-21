import datetime
import json
import os
import socket

import falcon
from bson import ObjectId, json_util

from smapy.utils import get_ms


class JSONSerializer(object):

    def process_request(self, req, resp):
        # req.stream corresponds to the WSGI wsgi.input environ variable,
        # and allows you to read bytes from the request body.
        #
        # See also: PEP 3333
        if req.content_length in (None, 0):
            # Nothing to do
            req.body = dict()
            return

        body = req.stream.read()
        if not body:
            raise falcon.HTTPBadRequest('Empty request body',
                                        'A valid JSON document is required.')

        try:
            # Load the body using bson.json_util to allow being passed
            # unserializable objects such as ObjectIDs or datetimes
            # req.context['body'] = json_util.loads(body.decode('utf-8'))
            req.body = json_util.loads(body.decode('utf-8'))

        except UnicodeDecodeError:
            raise falcon.HTTPBadRequest('Encoding Error',
                                        'Request must be encoded as UTF-8.') from None

        except ValueError:
            raise falcon.HTTPBadRequest('Malformed JSON',
                                        'A valid JSON document is required.') from None

    @staticmethod
    def _serial(obj):
        """JSON serializer for objects not serializable by default json code"""

        if isinstance(obj, datetime.datetime):
            return obj.isoformat()

        elif isinstance(obj, ObjectId):
            return str(obj)

        raise TypeError("{} is not JSON serializable".format(type(obj).__name__))

    def process_response(self, req, resp, resource):
        if not resp.body or isinstance(resp.body, str):
            # Nothing else to do here
            return

        elif req.context.get('internal'):
            # The request comes from another API instance, so we serialize
            # the body using json_util to avoid losing information.
            resp.body = json_util.dumps(resp.body, indent=4)

        else:
            # The request is external, so we "pretty print" the response.
            resp.body = json.dumps(resp.body, sort_keys=True, default=self._serial, indent=4)


class ResponseBuilder(object):

    def process_request(self, req, resp):
        req.context['in_ts'] = datetime.datetime.utcnow()

    def process_response(self, req, resp, resource):
        in_ts = req.context['in_ts']
        out_ts = req.context.get('out_ts') or datetime.datetime.utcnow()
        elapsed = req.context.get('elapsed') or get_ms(out_ts - in_ts)

        resp.body = {
            'status': resp.status,
            'pid': os.getpid(),
            'host': socket.gethostname(),
            'results': resp.body,
            'session': req.context.get('session'),
            'in_ts': in_ts,
            'out_ts': out_ts,
            'elapsed': elapsed
        }


class SessionHandler(object):
    """DEPRECATED."""

    def __init__(self, mongodb):
        self.mongodb = mongodb

    def process_request(self, req, resp):
        session = req.headers.get('API-SESSION')
        in_ts = datetime.datetime.utcnow()
        req.context['in_ts'] = in_ts

        if session:
            req.context['session'] = ObjectId(session)
            req.context['internal'] = True

        else:
            session = {
                'in_ts': in_ts,
                'body': req.body,
                'params': req.params,
                'pid': os.getpid(),
                'host': socket.gethostname(),
                'env': {k: v for k, v in req.env.items() if '.' not in k}
            }
            req.context['session'] = self.mongodb.session.insert(session)
            req.context['internal'] = False

    def process_response(self, req, resp, resource):
        in_ts = req.context['in_ts']
        out_ts = datetime.datetime.utcnow()
        req.context['out_ts'] = out_ts
        elapsed = get_ms(out_ts - in_ts)
        req.context['elapsed'] = elapsed

        if not req.context['internal']:
            session = req.context['session']
            match = {
                '_id': session
            }
            update = {
                '$set': {
                    'out_ts': out_ts,
                    'elapsed': get_ms(out_ts - in_ts),
                    'response': resp.body
                }
            }
            self.mongodb.session.update_one(match, update)
