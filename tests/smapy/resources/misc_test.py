import copy
from unittest.mock import call

from smapy.resources.misc import MultiProcess
from tests.utils import ResourceTestCase


class TestMultiProcess(ResourceTestCase):

    resource_class = MultiProcess

    def test_process(self):
        """Get the parameters and remotely call the resource multiple times."""

        # Set up
        message = {
            'processes': 2,
            'resource': 'a_resource',
            'something': 'else'
        }

        # Set up an invoke side_effect to be able to modify each message as required
        self.invoke_count = 0
        self.invoke_call_args_list = []

        def invoke_side_effect(runnable, messages, **kwargs):
            """Sets different results into message at each call."""

            # We store a copy of the call arguments before modifying anything
            call_args = call(runnable, copy.deepcopy(messages), **kwargs)
            self.invoke_call_args_list.append(call_args)

            if not isinstance(messages, list):
                messages = [messages]

            for message in messages:
                self.invoke_count += 1
                message['results'] = {
                    'calls': 1,
                    self.invoke_count: 'called'
                }

        self.resource.invoke.side_effect = invoke_side_effect

        # Actual call
        self.resource.process(message)

        # Asserts

        # Check if the message has been modified as required
        expected_message = {
            'something': 'else',
            'calls': 2,
            1: 'called',
            2: 'called',
            'details': [
                {
                    'calls': 1,
                    1: 'called'
                },
                {
                    'calls': 1,
                    2: 'called'
                }
            ]
        }
        self.assertEqual(expected_message, message)

        # Check if the invoke calls were the expected ones.
        expected_invoke_calls = [
            call('a_resource', [{'something': 'else'}, {'something': 'else'}],
                 concurrency=2, remote=True),
        ]
        self.assertEqual(expected_invoke_calls, self.invoke_call_args_list)
