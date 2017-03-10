"""
Fast test database - main module.
"""

import json
import os
import subprocess
import sys
from copy import copy
from time import sleep


def docker(*args):
    """Run Docker with the specified arguments and return the output."""

    return subprocess.check_output(('docker',) + args).decode().strip()


class DatabaseProvider(object):
    """Provide a database via Docker."""

    # These must be overridden in subclasses
    IMAGE = None
    PORT = None
    PASSWORD_ENV_VAR = None
    DATA_DIR = None
    ENGINE = None
    USER = None
    DATABASE = None

    @property
    def container_name(self):
        """The Docker container name."""
        return 'fast_database_{}_{}'.format(
            os.path.basename(os.getcwd()),
            self.ENGINE.rsplit('.', 1)[1],
        )

    def provide(self):
        """
        Ensure an instance of the database is started.

        :returns: a Django database dictionary to connect to the instance
        """

        # TODO: Randomize password
        password = 'fast_database'

        try:
            container = json.loads(docker('inspect', self.container_name))
            available = container[0]['State']['Running']
        except (LookupError, ValueError, subprocess.CalledProcessError):
            available = False

        if not available:
            # Delete the old container in case it's stopped
            try:
                docker('rm', '-f', self.container_name)
            except subprocess.CalledProcessError:
                pass

            docker(
                'run',
                '--detach',
                '--env', '{}={}'.format(self.PASSWORD_ENV_VAR, password),
                '--tmpfs={}'.format(self.DATA_DIR),
                '--publish', str(self.PORT),
                '--name', self.container_name,
                self.IMAGE,
            )
            # Give it time to start
            sleep(10)

        host, port = docker(
            'port', self.container_name, str(self.PORT)).split(':')
        port = int(port)

        return {
            'ENGINE': self.ENGINE,
            'NAME': self.DATABASE,
            'USER': self.USER,
            'PASSWORD': password,
            'HOST': host,
            'PORT': port,
        }


class PostgreSQL(DatabaseProvider):
    """Provide a PostgreSQL database via Docker."""

    IMAGE = 'postgres:latest'
    PORT = 5432
    PASSWORD_ENV_VAR = 'POSTGRES_PASSWORD'
    DATA_DIR = '/var/lib/postgresql/data'
    ENGINE = 'django.db.backends.postgresql_psycopg2'
    USER = 'postgres'
    DATABASE = 'postgres'


class MySQL(DatabaseProvider):
    """Provide a MySQL database via Docker."""

    IMAGE = 'mysql:latest'
    PORT = 3306
    PASSWORD_ENV_VAR = 'MYSQL_ROOT_PASSWORD'
    DATA_DIR = '/var/lib/mysql'
    ENGINE = 'django.db.backends.mysql'
    USER = 'root'
    DATABASE = 'mysql'  # TODO: is this correct?


PROVIDERS = {
    provider.ENGINE: provider
    for provider in [
        MySQL,
        PostgreSQL,
    ]
}


def fast_test_database(databases, test_commands=('test',)):
    """
    If running tests, start a database on a tmpfs and set it as the default
    connection.
    """

    if not any(test_command in sys.argv for test_command in test_commands):
        # Not under test, leave connections alone
        return databases

    database_type = databases['default']['ENGINE']

    if database_type not in PROVIDERS:
        return databases

    databases = copy(databases)
    databases['default'] = PROVIDERS[database_type]().provide()
    return databases


__all__ = (
    'fast_test_database',
)
