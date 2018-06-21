from unittest import TestCase
from unittest.mock import MagicMock, Mock

from bson import ObjectId


class ActionTestCase(TestCase):

    action_class = None

    def setUp(self):
        if not self.action_class:
            raise ValueError("action_class cannot be None! Please provide an actual Action class")

        self.api = MagicMock()

        self.session = ObjectId('57bee205ab17852928644d3e')
        self.request = MagicMock(context={'session': self.session})

        self.action_class.init(self.api)
        self.action = self.action_class(self.request)


class ResourceTestCase(TestCase):

    resource_class = None

    def setUp(self):
        if not self.resource_class:
            raise ValueError("resource_class cannot be None! "
                             "Please provide an actual resource class")

        self.api = MagicMock()

        self.session = ObjectId('57bee205ab17852928644d3e')
        self.request = MagicMock(context={'session': self.session})

        self.resource_class.init(self.api, 'a_route')
        self.resource = self.resource_class(self.request)

        # We will be never doing real invokes, so we mock the invoke method
        self.resource.invoke = Mock()
