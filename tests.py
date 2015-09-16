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


class FastDatabaseTest(unittest.TestCase):
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

        self.assertEqual(databases['default']['ENGINE'], PG_ENGINE)

        # Try connecting to it

        default_db = databases['default']
        conn = psycopg2.connect(
            database=default_db['NAME'],
            user=default_db['USER'],
            password=default_db['PASSWORD'],
            host=default_db['HOST'],
            port=default_db['PORT'],
        )
        cur = conn.cursor()
        cur.execute('SELECT VERSION()')
        (pg_version,) = cur.fetchone()
        self.assertTrue(pg_version.startswith('PostgreSQL 9'))


class IntegrationTest(unittest.TestCase):
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
        self.assertEqual(config, {
            'default': {
                'ENGINE': PG_ENGINE,
                'NAME': 'postgres',
                'USER': 'postgres',
                'PASSWORD': 'fast_database',
            },
        })
