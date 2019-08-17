# -*- coding: utf-8 -*-

from unittest import TestCase
from unittest.mock import MagicMock

from smapy.action import BaseAction


class TestBaseAction(TestCase):

    def test_run_local_ok(self):
        """insert_audit, copy_message, process and update_audit must be called."""

        # Set up
        class TestAction(BaseAction):
            name = 'test_action'
            insert_audit = MagicMock()
            update_audit = MagicMock()

            def process(self, message):
                """Modify the message."""
                message['a'] = 'modified message'

        api = MagicMock()
        api.auditdb = MagicMock()
        TestAction.init(api)

        resource = MagicMock()
        resource.context = {'session': 'a session'}
        test_action = TestAction(resource)

        # Actual call
        message = {'a': 'message'}
        test_action.run_local(message)

        # Asserts
        test_action.insert_audit.assert_called_once_with()
        test_action.update_audit.assert_called_once_with({'a': 'modified message'}, None)

        self.assertEqual(test_action.initial_message, {'a': 'message'})

    def test_run_local_exception(self):
        """If self.process raises an exception it must be properly inserted into audit."""

        # Set up
        class TestAction(BaseAction):
            name = 'test_action'
            insert_audit = MagicMock()
            update_audit = MagicMock()

            def process(self, message):
                """Modify the message and then raise an exception."""
                message['a'] = 'modified message'

                raise Exception("An Exception")

        api = MagicMock()
        api.auditdb = MagicMock()
        TestAction.init(api)

        insert_mock = MagicMock()
        insert_mock.return_value = 'an_audit_id'
        api.auditdb.actions.insert = insert_mock

        resource = MagicMock()
        resource.context = {'session': 'a session'}
        test_action = TestAction(resource)

        # Actual call
        message = {'a': 'message'}
        test_action.run_local(message)

        project_dir = __file__.replace('tests/test_action.py', '')

        # Asserts
        exception = [
            'Traceback (most recent call last):\n',
            '  File "{}smapy/action.py", line 63, in run_local\n'
            '    self.process(message)\n'.format(project_dir),
            '  File "{}tests/test_action.py", line 55, in process\n'
            '    raise Exception("An Exception")\n'.format(project_dir),
            'Exception: An Exception\n'
        ]

        test_action.insert_audit.assert_called_once_with()
        test_action.update_audit.assert_called_once_with({'a': 'modified message'}, exception)

        self.assertEqual(test_action.initial_message, {'a': 'message'})

    def test_run_local_systemexit(self):
        """If self.process raises an error it must be properly inserted into audit and risen."""

        # Set up
        class TestAction(BaseAction):
            name = 'test_action'
            insert_audit = MagicMock()
            update_audit = MagicMock()

            def process(self, message):
                """Modify the message and then raise an exception."""
                message['a'] = 'modified message'

                raise SystemExit()

        api = MagicMock()
        api.auditdb = MagicMock()
        TestAction.init(api)

        insert_mock = MagicMock()
        insert_mock.return_value = 'an_audit_id'
        api.auditdb.actions.insert = insert_mock

        resource = MagicMock()
        resource.context = {'session': 'a session'}
        test_action = TestAction(resource)

        # Actual call
        message = {'a': 'message'}
        self.assertRaises(SystemExit, test_action.run_local, message)

        project_dir = __file__.replace('tests/test_action.py', '')

        # Asserts
        exception = [
            'Traceback (most recent call last):\n',
            '  File "{}smapy/action.py", line 63, in run_local\n'
            '    self.process(message)\n'.format(project_dir),
            '  File "{}tests/test_action.py", line 103, in process\n'
            '    raise SystemExit()\n'.format(project_dir),
            'SystemExit\n'
        ]

        test_action.insert_audit.assert_called_once_with()
        test_action.update_audit.assert_called_once_with({'a': 'modified message'}, exception)

        self.assertEqual(test_action.initial_message, {'a': 'message'})
