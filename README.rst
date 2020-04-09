.. image:: https://www.dancerfly.com/static/brambling/images/all-dancers.gif

Dancerfly |travis|
++++++++++++++++++

.. |travis| image:: https://travis-ci.org/dancerfly/django-brambling.svg?branch=master
    :target: https://travis-ci.org/dancerfly/django-brambling

Naming
======

The name of this software is django-brambling. The name for use within the content of the application and for marketing purposes is Dancerfly.

Development Using Docker Compose
================================

As of April 2020, Dancerfly experimentally allows you to use Docker Compose to spin up a development environment with one line. If you prefer to use the older method of relying on your system Python, skip below to "Development Using System Python."

Prerequisites
-------------

These instructions assume you have the following software on your machine:

* `Docker Compose <https://docs.docker.com/compose/install/>`_

Installation instructions
-------------------------

Here's a one-liner to get you going. This runs a database container using PostgreSQL and an application container with the Django application. It will run the necessary initial database migrations.

.. code:: bash

   docker-compose up

Quick Tips
----------

Use ``docker-compose exec`` to run commands on a currently running application container or ``docker-compose run`` to start a container and run a command:

.. code:: bash

   docker-compose exec ./manage.py makemigrations
   docker-compose run pipenv install bleach

You can attach interactively to the Django process using this command:

.. code:: bash

   docker attach (docker-compose ps -q django)

Learn more about Docker Compose in `the documentation <https://docs.docker.com/compose/>`_.

Development Using System Python
===============================

Use these instructions if you'd rather not use Docker Compose.

Prerequisites
-------------

The installation instructions below assume you have the following software on your machine:

* `Python 2.7.x <https://www.python.org/downloads/release/python-2715/>`_
* `pipenv <https://docs.pipenv.org/install/#installing-pipenv>`_

Installation instructions
-------------------------

Here's a one-liner to get you going!

.. code:: bash

  pipenv install && pipenv run ./manage.py migrate && pipenv run ./manage.py runserver

This will install all project dependencies, set up the database, and start a server.
At this point you can visit `http://127.0.0.1:8000` in your favorite browser and see your locally running copy of Dancerfly!

.. note::

  If you experience issues installing the correct version of Django, try using ``pipenv install --sequential`` instead.
  See `github.com/pypa/pipenv/issues/2088 <https://github.com/pypa/pipenv/issues/2088>`_ for details.

.. image:: https://badges.gitter.im/Join%20Chat.svg
   :alt: Join the chat at https://gitter.im/littleweaver/django-brambling
   :target: https://gitter.im/littleweaver/django-brambling?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

Environment Variables (optional)
--------------------------------

Set the following optional environment variables in a local .env file if the default values don't work for you.
See `pipenv's documentation <https://docs.pipenv.org/advanced/#automatic-loading-of-env>`_ for more details.

============================================= ========================== =====================================================================================
Variable                                      Default                    Usage
============================================= ========================== =====================================================================================
``SECRET_KEY``                                ``'NOT_SECRET'``           Django `secret key`_
``DATABASE_URL``                              ``'sqlite:///db.sqlite3'`` 12-factor style database url ``[type]://[user][:password][@host][:port]/[dbname]``
                                                                         (e.g., ``postgres://root@localhost/dancerfly``)
``STRIPE_APPLICATION_ID``                     ``''``
``STRIPE_SECRET_KEY``                         ``''``
``STRIPE_PUBLISHABLE_KEY``                    ``''``
``STRIPE_TEST_APPLICATION_ID``                ``''``
``STRIPE_TEST_SECRET_KEY``                    ``''``
``STRIPE_TEST_PUBLISHABLE_KEY``               ``''``
``STRIPE_TEST_ORGANIZATION_ACCESS_TOKEN``     ``''``
``STRIPE_TEST_ORGANIZATION_PUBLISHABLE_KEY``  ``''``
``STRIPE_TEST_ORGANIZATION_REFRESH_TOKEN``    ``''``
``STRIPE_TEST_ORGANIZATION_USER_ID``          ``''``
============================================= ========================== =====================================================================================

.. _`secret key`: https://docs.djangoproject.com/en/1.11/ref/settings/#secret-key
