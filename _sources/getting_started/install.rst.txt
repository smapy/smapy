.. highlight:: shell

Installation
============

From PyPi
---------

The simplest and recommended way to install **Smapy** is using `pip`:

.. code-block:: console

    pip install smapy

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/

From sources
------------

The sources for **Smapy** can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/csala/smapy

Or download the `tarball`_:

.. code-block:: console

    $ curl  -OL https://github.com/csala/smapy/tarball/master

Once you have a copy of the source, you can install it running the next command inside the
project folder:

.. code-block:: console

    $ make install

.. _Github repo: https://github.com/csala/smapy
.. _tarball: https://github.com/csala/smapy/tarball/master

Development
-----------

If you are installing **Smapy** in order to modify its code, the installation must be done
from its sources, in the editable mode, and also including some additional dependencies in
order to be able to run the tests and build the documentation:

.. code-block:: console

    make install-develop
