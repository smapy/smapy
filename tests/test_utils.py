# -*- coding: utf-8 -*-

import datetime
from unittest import TestCase
from unittest.mock import Mock, patch

from smapy import utils


class Shape(object):
    pass


class FourLeggedShape(Shape):
    pass


class ThreeLeggedShape(Shape):
    pass


class Square(FourLeggedShape):
    pass


class SubClassTest(TestCase):
    def test_non_recursive(self):
        s = Shape
        r = utils.find_subclasses(s, recursive=False)
        self.assertIsInstance(r, list)
        self.assertIn(FourLeggedShape, r)
        self.assertIn(ThreeLeggedShape, r)
        self.assertNotIn(Square, r)
        self.assertEqual(2, len(r))

    def test_recursive(self):
        s = Shape
        r = utils.find_subclasses(s, recursive=True)
        self.assertIsInstance(r, list)
        self.assertIn(FourLeggedShape, r)
        self.assertIn(ThreeLeggedShape, r)
        self.assertIn(Square, r)
        self.assertEqual(3, len(r))

    def test_no_subclasses_recursive(self):
        s = ThreeLeggedShape
        r = utils.find_subclasses(s, recursive=True)
        self.assertIsInstance(r, list)
        self.assertEqual(0, len(r))

    def test_no_subclasses_non_recursive(self):
        s = ThreeLeggedShape
        r = utils.find_subclasses(s, recursive=False)
        self.assertIsInstance(r, list)
        self.assertEqual(0, len(r))

    def test_with_subclasses_recursive(self):
        s = FourLeggedShape
        r = utils.find_subclasses(s, recursive=True)
        self.assertIsInstance(r, list)
        self.assertIn(Square, r)
        self.assertEqual(1, len(r))

    def test_non_type(self):
        s = Shape()
        b = True
        self.assertRaises(AttributeError, utils.find_subclasses, s, b)


class SumDictsTest(TestCase):
    def test_with_illegal(self):
        a = 1
        b = {'test': 1}
        self.assertRaises(TypeError, utils.sum_dicts, a, b)

    def test_with_none(self):
        a = None
        b = None
        r = utils.sum_dicts(a, b)
        self.assertEqual({}, r)

    def test_empty(self):
        a = {}
        b = {}
        r = utils.sum_dicts(a, b)
        self.assertEqual({}, r)

    def test_numbers(self):
        a = {'a': 1}
        b = {'a': 2}
        r = utils.sum_dicts(a, b)
        self.assertEqual({'a': 3}, r)

    def test_numbers_different_key(self):
        a = {'a': 1}
        b = {'b': 2}
        r = utils.sum_dicts(a, b)
        self.assertEqual({'a': 1, 'b': 2}, r)

    def test_lists(self):
        a = {'a': [1]}
        b = {'a': [2]}
        r = utils.sum_dicts(a, b)
        self.assertEqual({'a': [1, 2]}, r)

    def test_lists_different_keys(self):
        a = {'a': [1]}
        b = {'b': [2]}
        r = utils.sum_dicts(a, b)
        self.assertEqual({'a': [1], 'b': [2]}, r)

    def test_mix(self):
        a = {'a': [1]}
        b = {'a': [2], 'b': 3}
        r = utils.sum_dicts(a, b)
        self.assertEqual({'b': 3, 'a': [1, 2]}, r)

    def test_longer_mix(self):
        a = {'a': 1, 'b': 2, 'c': [1]}
        b = {'b': 3, 'c': [4], 'd': [5]}
        r = utils.sum_dicts(a, b)
        self.assertEqual({'c': [1, 4], 'b': 5, 'd': [5], 'a': 1}, r)


class ReadConfTest(TestCase):

    def test_no_conf_file(self):
        # run
        conf = utils.read_conf(None)

        # assert
        self.assertEqual(conf, dict())

    def test_illegal_filename(self):
        s = '/i_dont_exists/at_all.csv'
        self.assertRaises(FileNotFoundError, utils.read_conf, s)

    @patch('smapy.utils.os')
    @patch('smapy.utils.configparser.ConfigParser')
    def test_valid_conf_dict(self, config_parser_mock, os_mock):
        os_mock.path.is_file.return_value = True

        config_mock = Mock()
        config_parser_mock.return_value = config_mock
        config_mock.items.return_value = [('section_1', {'a': '1'}),
                                          ('section_2', {'b': '{"test": 1}'})]
        r = utils.read_conf('test.ini')

        self.assertEqual({'section_1': {'a': 1}, 'section_2': {'b': {'test': 1}}}, dict(r))

    @patch('smapy.utils.os')
    @patch('smapy.utils.configparser.ConfigParser')
    def test_invalid_conf_dict(self, config_parser_mock, os_mock):
        os_mock.path.is_file.return_value = True

        config_mock = Mock()
        config_parser_mock.return_value = config_mock
        config_mock.items.return_value = [('section_1', {'a': '1'}),
                                          ('section_2', {'b': '{"test": esdfsdf}'})]

        # variable 'esdfsdf' will not exist!
        self.assertRaises(NameError, utils.read_conf, 'test.ini')


class GetMsTest(TestCase):

    def test_get_ms_some_milliseconds(self):
        delta = datetime.timedelta(milliseconds=15, microseconds=222)
        ms = utils.get_ms(delta)
        self.assertEqual(15.222, ms)

    def test_get_ms_days(self):
        delta = datetime.timedelta(days=3, seconds=34, milliseconds=115, microseconds=222)
        ms = utils.get_ms(delta)
        self.assertEqual(259234115.222, ms)


class TestSetenv(TestCase):
    @patch('smapy.utils.os')
    def test_setenv_empty(self, os_mock):
        os_mock.environ = {}
        utils.setenv({'a': 'parameter'})
        self.assertEqual({'a': 'parameter'}, os_mock.environ)

    @patch('smapy.utils.os')
    def test_setenv_not_empty(self, os_mock):
        os_mock.environ = {
            'a': 'is already here',
            'something': 'else'
        }
        utils.setenv({
            'a': 'parameter',
            'another': 'parameter'
        })
        expected = {
            'a': 'is already here',
            'something': 'else',
            'another': 'parameter'
        }
        self.assertEqual(expected, os_mock.environ)
