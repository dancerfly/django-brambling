Dance event registration and ticketing app. In development.

Naming
======

The name of this software is django-brambling. The name for use within the content of the application and for marketing purposes is Dancerfly.

Development
=============

Prerequisites
-------------

The installation instructions below assume you have the following software on your machine:

* `Python 2.7.x <http://www.python.org/download/releases/2.7.6/>`_
* `Ruby <https://www.ruby-lang.org/en/installation/>`_
* `Pip <https://pip.readthedocs.org/en/latest/installing.html>`_
* `virtualenv <http://www.virtualenv.org/en/latest/virtualenv.html#installation>`_ (optional)
* `virtualenvwrapper <http://virtualenvwrapper.readthedocs.org/en/latest/install.html>`_ (optional)

Installation instructions
-------------------------

If you are using virtualenv or virtualenvwrapper, create and activate an environment. E.g.,

.. code:: bash

    mkvirtualenv brambling # Using virtualenvwrapper.

Then, to install:

.. code:: bash

    # Clone django-brambling to a location of your choice.
    git clone https://github.com/littleweaver/django-brambling.git

    # Install django-brambling.
    pip install --no-deps -e django-brambling

    # Install python requirements. This may take a while.
    pip install -r django-brambling/test_project/requirements.txt

    # Install ruby requirements. This could also take a second.
    gem install bundler # Ensure you have Bundler. May need sudo.
    bundle install --gemfile django-brambling/Gemfile # Install Ruby requirements.

Get it running
--------------

.. code:: bash

    cd django-brambling/test_project
    python manage.py syncdb    # Create/sync the database.
    python manage.py runserver # Run the server!

Then, navigate to ``http://127.0.0.1:8000/`` in your favorite web browser!
