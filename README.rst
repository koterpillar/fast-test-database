Fast test database
==================

Use a pure in-memory database for running Django tests.

Usage
-----

In ``settings.py``:

.. code:: python

    from fast_test_database import fast_test_database

    DATABASES = fast_test_database(DATABASES)

    # Or:
    DATABASES = fast_test_database(DATABASES,
                                   test_commands=('test', 'harvest'))

    # Or:
    DATABASES = fast_test_database(DATABASES,
                                   version='5.7')

This will be a no-op except for ``./manage.py test``, when an in-memory
database will be automatically started and supplied to the application.

Details
-------

The in-memory database is a full PostgreSQL or MySQL instance started
using Docker, using tmpfs for storing the data. A single container will
be started if not yet running. It will not be shut down automatically,
and instead reused for subsequent tests.

The type of the database (PostgreSQL or MySQL) is chosen based on the
existing default database engine.

The default version of the database (PostgreSQL or MySQL) is latest.
But it can be specified by version parameter.
