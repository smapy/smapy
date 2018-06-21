import logging
from abc import ABCMeta, abstractmethod

import falcon
import requests
from bson import ObjectId, json_util

# from smapy.logging import SessionFilter


class RemoteRunnable(object):

    route = '/_remote'

    @classmethod
    def init(cls, api):
        cls.api = api
        cls.mongodb = api.mongodb
        cls.endpoint = api.endpoint + cls.route
        cls.name = cls.__name__
        cls.logger = logging.getLogger(cls.name)

        cls.rq_session = requests.Session()

        pool_size = api.conf['api'].get('remote_pool_size', 1024)
        adapter = requests.adapters.HTTPAdapter(pool_connections=pool_size,
                                                pool_maxsize=pool_size,
                                                pool_block=True)
        cls.rq_session.mount('http://', adapter)
        cls.rq_session.mount('https://', adapter)

    def __init__(self, runnable):
        self.runnable = runnable
        self.name = self.__class__.__name__ + '({})'.format(runnable.name)
        logger = logging.getLogger(self.name)
        self.logger = logging.LoggerAdapter(logger, {'session': runnable.session})

    def run(self, message):
        self.logger.debug('Running remotly')

        data = json_util.dumps({
            'runnable': self.runnable.name,
            'message': message,
        })
        headers = {'API-SESSION': str(self.runnable.session)}

        response = self.rq_session.post(self.endpoint, data=data, headers=headers)

        self.logger.debug(response.text)

        try:
            response_json = json_util.loads(response.text)

        except ValueError:
            self.logger.error('Invalid response format: %s', response.text)
            raise falcon.HTTPInternalServerError(
                self.name, 'Invalid remote response format') from None

        status = response_json['status']
        self.logger.debug('Remote status: %s', status)

        if status != falcon.HTTP_200:
            self.logger.error('Remote status not OK: %s', response.text)
            raise falcon.HTTPInternalServerError(self.name, 'Error status: {}'.format(status))

        message.update(response_json['results']['message'])

    @classmethod
    def on_post(cls, req, resp):
        """Run the indicated runnable passing the given message."""
        try:
            message = req.body['message']
            runnable = req.body['runnable']

        except KeyError as ke:
            raise falcon.HTTPMissingParam(ke.args[0]) from None

        session = req.headers.get('API-SESSION')
        if not session:
            raise falcon.HTTPMissingParam('API-SESSION')

        req.context['session'] = ObjectId(session)
        req.context['internal'] = True

        cls.logger.debug('Running runnable %s', runnable, extra={'session': session})

        runnable_class = cls.api.runnables[runnable]
        runnable_class(req).run_local(message)

        resp.body = {
            'runnable': runnable,
            'message': message,
        }
        cls.logger.debug('runnable %s status: OK', runnable, extra={'session': session})


class RunnableMeta(ABCMeta):
    """Metaclass to be used by the Runnable class.

    This metaclass gives each Runnable class a custom "name"
    attribute derived from the class model and name.
    This has to be done here, in a metaclass, because otherwise we are
    not able to access the  module name until the class is instantiated.
    """

    name = None

    def __init__(self, name, bases, dict):
        if 'name' not in dict:
            # Set the default name only if not explicitly defined in the class
            module_name = self.__module__.rsplit('.', 1)[-1]
            self.name = '.'.join((module_name, name))


class Runnable(metaclass=RunnableMeta):

    def __init__(self, request):
        self.request = request
        self.context = request.context
        self.session = request.context['session']
        self.logger = logging.LoggerAdapter(self.logger, {'session': self.session})

    @classmethod
    def init(cls, api):
        cls.api = api
        cls.mongodb = api.mongodb
        cls.auditdb = api.auditdb
        cls.conf = api.conf
        cls.logger = logging.getLogger(cls.name)

    @abstractmethod
    def run_local(self, message):
        """The actual runnable code should be implemented here by subclasses."""

    def check_session_alive(self):
        match = {
            '_id': self.session
        }
        projection = {
            '_id': 0,
            'alive': 1
        }
        session = self.mongodb.session.find_one(match, projection=projection)
        if not (session and session.get('alive')):
            raise falcon.HTTPInternalServerError(
                self.name, 'Session {} not alive'.format(self.session))

    def run(self, message, remote=False, callback=None):
        self.check_session_alive()

        if remote:
            RemoteRunnable(self).run(message)

        else:
            self.run_local(message)

        if callback:
            callback(message)
