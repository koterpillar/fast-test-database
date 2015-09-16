"""
Test supplying the fast database.
"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

import json
import os
import subprocess
import sys
import unittest
from contextlib import contextmanager

import psycopg2

from fast_test_database import fast_test_database


PG_ENGINE = 'django.db.backends.postgresql_psycopg2'
SQLITE_ENGINE = 'django.db.backends.sqlite3'


class TestCase(unittest.TestCase):
    """Base test case."""

    def assert_postgres(self, database):
        """
        Verify that the specified dict is for a valid PostgreSQL database
        connection.
        """

        self.assertEqual(
            database['ENGINE'],
            PG_ENGINE,
            "Engine must be {0}, not {1}.".format(
                PG_ENGINE, database['ENGINE'])
        )

        # Try connecting to it
        conn = psycopg2.connect(
            database=database['NAME'],
            user=database['USER'],
            password=database['PASSWORD'],
            host=database['HOST'],
            port=database['PORT'],
        )
        cur = conn.cursor()
        cur.execute('SELECT VERSION()')
        (pg_version,) = cur.fetchone()
        self.assertTrue(
            pg_version.startswith('PostgreSQL 9'),
            "PostgreSQL 9 expected, got {0}".format(pg_version)
        )


class FastDatabaseTest(TestCase):
    """Test calling fast_test_database."""

    ORIGINAL_DATABASES = {
        'default': {
            'ENGINE': SQLITE_ENGINE,
            'NAME': '/some/db.sqlite3',
        }
    }

    @contextmanager
    def mock_sys_argv(self, *args):
        """Mock sys.argv for the life of the context manager."""

        original_argv = sys.argv
        sys.argv = list(args)
        try:
            yield
        finally:
            sys.argv = original_argv

    def test_normal_run(self):
        """Test calling fast_test_database while not inside tests."""

        with self.mock_sys_argv('python', './manage.py', 'runserver'):
            databases = fast_test_database(self.ORIGINAL_DATABASES)

        self.assertEqual(databases, self.ORIGINAL_DATABASES)

    def test_change_db(self):
        """Test calling fast_test_database inside tests."""

        with self.mock_sys_argv('python', './manage.py', 'test'):
            databases = fast_test_database(self.ORIGINAL_DATABASES)

        self.assert_postgres(databases['default'])


class IntegrationTest(TestCase):
    """Test supplying the fast database to the test application."""

    TEST_APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'test_app')

    def run_manage(self, *args):
        """
        Run manage.py of the test application with the specified arguments.
        """

        previous_wd = os.getcwd()
        os.environ['PYTHONPATH'] = previous_wd
        os.chdir('test_app')
        try:
            return subprocess.check_output(('./manage.py',) + args)\
                .decode().strip()
        finally:
            os.chdir(previous_wd)

    def database_config(self, output):
        """
        Parse the database configuration from the test application output.

        See test_app/test_app/settings.py for the code printing it.
        """

        lines = output.split('\n')
        start = lines.index("--- database configuration ---")
        end = lines.index("--- end database configuration ---")
        configuration = '\n'.join(lines[start + 1:end])
        return json.loads(configuration)

    def test_normal_database(self):
        """Test the database configuration under normal running."""

        config = self.database_config(self.run_manage('check'))
        self.assertEqual(config, {
            'default': {
                'ENGINE': SQLITE_ENGINE,
                'NAME': os.path.join(self.TEST_APP_DIR, 'db.sqlite3'),
            },
        })

    def test_fast_database(self):
        """Test the supplied fast database."""

        config = self.database_config(self.run_manage('test', '--noinput'))

        self.assert_postgres(config['default'])
