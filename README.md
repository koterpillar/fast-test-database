Fast test database
==================

Use a pure in-memory database for running Django tests

Usage
-----

In `settings.py`:

```python
from fast_test_database import fast_test_database

DATABASES = fast_test_database(DATABASES)
```

This will be a no-op except for `./manage.py test`, when an in-memory database
will be automatically started and supplied to the application.

Details
-------

The in-memory database is a full PostgreSQL instance started using Docker,
using tmpfs for storing the data. A single container will be started if not yet
running. It will not be shut down automatically, and instead reused for
subsequent tests.
