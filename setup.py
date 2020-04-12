#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.md') as history_file:
    history = history_file.read()

install_requires = [
    'concurrent-log-handler>=0.9.12,<0.10',
    'falcon>=1.4.1,<2',
    'gevent>=1.2.2,<2',
    'gunicorn>=19.8.1,<21',
    'pymongo>=3.6.1,<4',
    'requests>=2.19.1,<3',
]

tests_require = [
    'pytest>=3.4.2',
    'pytest-cov>=2.6.0',
]

development_requires = [
    # general
    'pip>=9.0.1',
    'bumpversion>=0.5.3,<0.6',
    'watchdog>=0.8.3,<0.11',

    # docs
    'm2r>=0.2.0,<0.3',
    'nbsphinx>=0.5.0,<0.7',
    'Sphinx>=1.7.1,<3',
    'sphinx_rtd_theme>=0.2.4,<0.5',

    # style check
    'flake8>=3.7.7,<4',
    'isort>=4.3.4,<5',

    # fix style issues
    'autoflake>=1.1,<2',
    'autopep8>=1.4.3,<2',

    # distribute on PyPI
    'twine>=1.10.0,<4',
    'wheel>=0.30.0',

    # Advanced testing
    'coverage>=4.5.1,<6',
    'tox>=2.9.1,<4',

    # Documentation style
    'doc8==0.8.0,<0.9',
    'pydocstyle==3.0.0,<4',
]

setup_requires = [
    'pytest-runner>=2.11.1',
]

setup(
    author='Carles Sala',
    author_email='carles@pythiac.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Simple Modular API written in Python.",
    entry_points = {
        'console_scripts': [
            'smapy=smapy.cli:main'
        ],
    },
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
    python_requires='>=3.5',
    setup_requires=setup_requires,
    test_suite='tests',
    tests_require=tests_require,
    url='https://github.com/csala/smapy',
    version='0.0.4.dev0',
    zip_safe=False,
)
