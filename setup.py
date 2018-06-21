#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.md') as history_file:
    history = history_file.read()

install_requires = [
    'ConcurrentLogHandler>=0.9.1',
    'falcon>=1.4.1',
    'gevent>==1.2.2',
    'gunicorn>=19.8.1',
    'pymongo>=3.6.1',
]

tests_require = [
    'mock>=2.0.0',
    'pytest>=3.4.2',
]

development_requires = [
    'autoflake>=1.1',
    'autopep8>=1.3.5',
    'bumpversion>=0.5.3',
    'coverage>=4.5.1',
    'flake8>=3.5.0',
    'isort>=4.3.4',
    'pip>=9.0.1',
    'pycodestyle==2.3.1',
    'pyflakes==1.6.0',
    'tox>=2.9.1',
    'twine>=1.10.0',
    'wheel>=0.30.0',
]

setup_requires = [
    'pytest-runner>=2.11.1',
]

setup(
    author='Carles Sala Cladellas',
    author_email='carles@pythiac.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    description="Simple Modular API written in Python.",
    extras_require={
        'test': tests_require,
        'dev': tests_require + development_requires,
    },
    include_package_data=True,
    install_requires=install_requires,
    keywords='api',
    license="MIT license",
    long_description=readme + '\n\n' + history,
    long_description_content_type='text/markdown',
    name='smapy',
    packages=find_packages(include=['smapy*']),
    setup_requires=setup_requires,
    test_suite='tests',
    tests_require=tests_require,
    url='https://github.com/csala/smapy',
    version='0.0.1-dev',
    zip_safe=False,
)
