"""
Test supplying the fast database.
"""

import json
import os
import subprocess
import sys
import unittest
from contextlib import contextmanager

import MySQLdb

import psycopg2

from fast_test_database import fast_test_database


PG_ENGINE = "django.db.backends.postgresql"
PG_ENGINE_OLD = "django.db.backends.postgresql_psycopg2"
MYSQL_ENGINE = "django.db.backends.mysql"
SQLITE_ENGINE = "django.db.backends.sqlite3"

SQLITE_SETTINGS = {
    "default": {
        "ENGINE": SQLITE_ENGINE,
        "NAME": "/some/db.sqlite3",
    },
}

MYSQL_SETTINGS = {
    "default": {
        "ENGINE": MYSQL_ENGINE,
        "NAME": "some",
    },
}

PG_SETTINGS = {
    "default": {
        "ENGINE": PG_ENGINE,
        "NAME": "some",
    },
}

PG_SETTINGS_OLD = {
    "default": {
        "ENGINE": PG_ENGINE_OLD,
        "NAME": "some",
    },
}


class TestCase(unittest.TestCase):
    """Base test case."""

    def assert_engine(self, expected_engine, database):
        """
        Verify that the specified dict has the expected database engine
        specified.
        """

        self.assertEqual(
            database["ENGINE"],
            expected_engine,
            f"Engine must be {expected_engine}, not {database['ENGINE']}",
        )

    def _select_version(self, connection):
        """Get the database version for the connection."""

        cur = connection.cursor()
        cur.execute("SELECT VERSION()")
        (version,) = cur.fetchone()
        return version

    def assert_postgres(self, database, target_version, engine=None):
        """
        Verify that the specified dict is for a valid PostgreSQL database
        connection.

        :param engine: The expected PostgreSQL engine
        """

        self.assert_engine(engine or PG_ENGINE, database)

        # Try connecting to it
        conn = psycopg2.connect(
            database=database["NAME"],
            user=database["USER"],
            password=database["PASSWORD"],
            host=database["HOST"],
            port=database["PORT"],
        )
        version = self._select_version(conn)
        self.assertTrue(
            version.startswith(f"PostgreSQL {target_version}"),
            f"PostgreSQL {target_version} expected, got {version}",
        )

    def assert_mysql(self, database, target_version):
        """
        Verify that the specified dict is for a valid MySQL database
        connection.
        """

        self.assert_engine(MYSQL_ENGINE, database)

        conn = MySQLdb.connect(
            db=database["NAME"],
            user=database["USER"],
            passwd=database["PASSWORD"],
            host=database["HOST"],
            port=database["PORT"],
        )
        version = self._select_version(conn)
        self.assertTrue(
            version.startswith(target_version),
            f"MySQL {target_version} expected, got {version}"
        )


class FastDatabaseTest(TestCase):
    """Test calling fast_test_database."""

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

        for config in (
            MYSQL_SETTINGS,
            PG_SETTINGS,
            SQLITE_SETTINGS,
        ):
            with self.mock_sys_argv("python", "./manage.py", "runserver"):
                databases = fast_test_database(config)

            self.assertEqual(databases, config)

    def test_change_db_sqlite(self):
        """
        Test calling fast_test_database inside tests with SQLite configured.
        """

        with self.mock_sys_argv("python", "./manage.py", "test"):
            databases = fast_test_database(SQLITE_SETTINGS)

        self.assertEqual(databases["default"], SQLITE_SETTINGS["default"])

    def test_change_db_mysql(self):
        """
        Test calling fast_test_database inside tests with MySQL configured.
        """

        with self.mock_sys_argv("python", "./manage.py", "test"):
            databases = fast_test_database(MYSQL_SETTINGS, version="8.3")

        self.assert_mysql(databases["default"], "8.3")

    def test_change_db_postgres(self):
        """
        Test calling fast_test_database inside tests with PostgreSQL
        configured.
        """

        with self.mock_sys_argv("python", "./manage.py", "test"):
            databases = fast_test_database(PG_SETTINGS, version=16)

        self.assert_postgres(databases["default"], 16)

    def test_change_db_postgres_old(self):
        """
        Test calling fast_test_database inside tests with PostgreSQL
        configured using the old backend alias.
        """

        with self.mock_sys_argv("python", "./manage.py", "test"):
            databases = fast_test_database(PG_SETTINGS_OLD, version=15)

        self.assert_postgres(databases["default"], 15, engine=PG_ENGINE_OLD)


class IntegrationTest(TestCase):
    """Test supplying the fast database to the test application."""

    TEST_APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_app")

    def run_manage(self, *args):
        """
        Run manage.py of the test application with the specified arguments.
        """

        previous_wd = os.getcwd()
        os.environ["PYTHONPATH"] = previous_wd
        os.chdir("test_app")
        try:
            return subprocess.check_output(("./manage.py",) + args).decode().strip()
        finally:
            os.chdir(previous_wd)

    def database_config(self, output):
        """
        Parse the database configuration from the test application output.

        See test_app/test_app/settings.py for the code printing it.
        """

        lines = output.split("\n")
        start = lines.index("--- database configuration ---")
        end = lines.index("--- end database configuration ---")
        configuration = "\n".join(lines[start + 1 : end])
        return json.loads(configuration)

    @contextmanager
    def set_database_config(self, config):
        """Set the DATABASES setting of the test application."""

        os.environ["DATABASES"] = json.dumps(config)
        try:
            yield
        finally:
            del os.environ["DATABASES"]

    def test_normal_database(self):
        """Test the database configuration under normal running."""

        for config in (
            MYSQL_SETTINGS,
            PG_SETTINGS,
            SQLITE_SETTINGS,
        ):
            with self.set_database_config(config):
                actual = self.database_config(self.run_manage("check"))

            self.assertEqual(actual, config)

    def test_fast_database_postgresql(self):
        """Test the supplied fast database."""

        with self.set_database_config(PG_SETTINGS):
            config = self.database_config(self.run_manage("test", "--noinput"))

        self.assert_postgres(config["default"], "15")

    def test_fast_database_mysql(self):
        """Test the supplied fast database."""

        with self.set_database_config(MYSQL_SETTINGS):
            config = self.database_config(self.run_manage("test", "--noinput"))

        self.assert_mysql(config["default"], "8.0")
