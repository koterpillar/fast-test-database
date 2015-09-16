"""
Fast test database - main module.
"""

import subprocess
import sys
from copy import copy
from time import sleep

IMAGE = 'postgres:latest'
PORT = 5432


def docker(*args):
    """Run Docker with the specified arguments and return the output."""

    return subprocess.check_output(('docker',) + args).decode().strip()


def fast_test_database(databases):
    """
    If running tests, start a database on a tmpfs and set it as the default
    connection.
    """

    test_commands = ('test',)

    if not any(test_command in sys.argv for test_command in test_commands):
        # Not under test, leave connections alone
        return databases

    # TODO: Determine the container name from the application name or path
    container_name = 'fast_database'

    # TODO: Randomize password
    password = 'fast_database'

    try:
        docker('inspect', container_name)
    except subprocess.CalledProcessError:
        # TODO: find tmpfs
        docker(
            'run',
            '-d',
            '-e', 'POSTGRES_PASSWORD=' + password,
            '-P',
            '--name', container_name,
            IMAGE,
        )
        # Give it time to start
        sleep(10)

    host, port = docker('port', container_name, str(PORT)).split(':')

    databases = copy(databases)
    databases['default'] = {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': password,
        'HOST': host,
        'PORT': port,
    }
    return databases

__all__ = (
    'fast_test_database',
)
