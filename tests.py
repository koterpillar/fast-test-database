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
import unittest


class IntegrationTest(unittest.TestCase):
    """Test supplying the fast database to the test application."""

    TEST_APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'test_app')

    def run_manage(self, *args):
        """
        Run manage.py of the test application with the specified arguments.
        """

        previous_wd = os.getcwd()
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
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(self.TEST_APP_DIR, 'db.sqlite3'),
            },
        })

    def test_fast_database(self):
        """Test the supplied fast database."""

        config = self.database_config(self.run_manage('test', '--noinput'))
        self.assertEqual(config, {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'test_postgres',
                'USER': 'postgres',
                'PASSWORD': 'test_password',
            },
        })
