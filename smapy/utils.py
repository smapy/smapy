# -*- coding: utf-8 -*-

import configparser
import copy
import importlib
import os
import pkgutil
from collections import defaultdict


def find_subclasses(parent_class, recursive=False):
    """Find the subclasses of a given parent class."""
    subclasses = parent_class.__subclasses__()

    if recursive:
        for i in range(0, len(subclasses)):
            temp = find_subclasses(subclasses[i])
            if temp:
                subclasses.extend(temp)

    return subclasses


def read_conf(conf_file):
    conf = configparser.ConfigParser(interpolation=None)
    conf.optionxform = str    # Prevent lowercase keys

    if not os.path.isfile(conf_file):
        raise FileNotFoundError("File {} not found".format(conf_file))

    conf.read(conf_file)

    conf_dict = defaultdict(lambda: defaultdict(lambda: None))

    for section, params in conf.items():
        for key, value in params.items():
            conf_dict[section][key] = eval(value)

    return conf_dict


def setenv(conf):
    for key, value in conf.items():
        if key not in os.environ:
            os.environ[key] = value


def get_bool(message, key, default=False):
    if key not in message:
        return default

    value = message.get(key)
    if not value:
        return True

    string = str(value).lower()
    if string in ['true', 'yes', 'y', '1']:
        return True

    elif string in ['false', 'no', 'n', '0']:
        return False

    raise ValueError('Invalid boolean: {}'.format(string))


def sum_dicts(a, b):
    """Sum the values of the two dicts, no matter which type they are.

    >>> sum_dicts({}, {})
    {}
    >>> sum_dicts({'a': 1}, {'a': 2})
    {'a': 3}
    >>> sum_dicts({'a': [1]}, {'a': [2], 'b': 3})
    {'b': 3, 'a': [1, 2]}
    >>> sum_dicts({'a': 1, 'b': 2, 'c': [1]}, {'b': 3, 'c': [4], 'd': [5]})
    {'c': [1, 4], 'b': 5, 'd': [5], 'a': 1}
    """

    merged = dict()
    if a is None or b is None:
        return a if a else b or {}

    for key in set(a) | set(b):
        value_a = a.get(key, type(b.get(key))())
        value_b = b.get(key, type(a.get(key))())
        if isinstance(value_a, dict) and isinstance(value_b, dict):
            merged[key] = sum_dicts(value_a, value_b)

        else:
            merged[key] = value_a + value_b

    return merged


def safecopy(obj):
    # if isinstance(obj, dict):
    #     clone = dict()
    #     for key, value in obj.items():
    #         clone[key] = safecopy(value)

    #     return clone

    # elif isinstance(obj, bs4.BeautifulSoup):
    #     return str(obj)

    return copy.deepcopy(obj)


def get_ms(delta):
    """Convert a datetime.timedelta into the corresponding milliseconds.

    >>> from datetime import timedelta
    >>> get_ms(timedelta(1, 1, 1, 1))
    86401001.001
    >>> get_ms(timedelta(days=1))
    86400000.0
    >>> get_ms(timedelta(seconds=15))
    15000.0
    >>> get_ms(timedelta(milliseconds=15, microseconds=222))
    15.222
    """
    return delta.days * 24 * 60 * 60 * 1000 + delta.seconds * 1000 + delta.microseconds / 1000


def find_submodules(package):
    if isinstance(package, str):
        package = importlib.import_module(package)

    submodules = list()

    # Otherwise it is not a package but a module
    if hasattr(package, '__path__'):
        for _, name, __ in pkgutil.iter_modules(package.__path__):
            full_name = package.__name__ + '.' + name
            module = importlib.import_module(full_name)
            submodules.append(module)

    return submodules
