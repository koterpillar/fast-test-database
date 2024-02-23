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

    return subprocess.check_output(("docker",) + args).decode().strip()


class DatabaseProvider(object):
    """Provide a database via Docker."""

    # These must be overridden in subclasses
    IMAGE = None
    PORT = None
    PASSWORD_ENV_VAR = None
    CUSTOM_ENV = None
    DATA_DIR = None
    ENGINE_MATCH = None
    USER = None
    DATABASE = None

    def __init__(self, version=None):
        self.version = version

    @property
    def container_name(self):
        """The Docker container name."""
        return f"fast_database_{os.path.basename(os.getcwd())}_{self.image.replace('/', '.').replace(':', '-')}"

    @property
    def image(self):
        """The Docker image."""
        return f"{self.IMAGE}:{self.version or 'latest'}"

    def provide(self, engine):
        """
        Ensure an instance of the database is started.

        :returns: a Django database dictionary to connect to the instance
        """

        # TODO: Randomize password
        password = "fast_database"

        try:
            container = json.loads(docker("inspect", self.container_name))
            available = container[0]["State"]["Running"]
        except (LookupError, ValueError, subprocess.CalledProcessError):
            available = False

        if not available:
            # Delete the old container in case it's stopped
            try:
                docker("rm", "-f", self.container_name)
            except subprocess.CalledProcessError:
                pass

            args = ["run", "--detach", "--env", f"{self.PASSWORD_ENV_VAR}={password}"]

            # Add custom environment variables
            if self.CUSTOM_ENV:
                for k, v in self.CUSTOM_ENV.items():
                    args.extend(["--env", f"{k}={v}"])

            args.extend(
                [
                    f"--tmpfs={self.DATA_DIR}",
                    "--publish",
                    str(self.PORT),
                    "--name",
                    self.container_name,
                    self.image,
                ]
            )

            docker(*args)
            # Give it time to start
            sleep(10)

        """example return values of docker()
        0.0.0.0:49153
        0.0.0.0:49153\n:::49153
        """
        host, port = (
            docker("port", self.container_name, str(self.PORT))
            .splitlines()[0]
            .split(":")
        )
        port = int(port)

        return {
            "ENGINE": engine,
            "NAME": self.DATABASE,
            "USER": self.USER,
            "PASSWORD": password,
            "HOST": host,
            "PORT": port,
        }


class PostgreSQL(DatabaseProvider):
    """Provide a PostgreSQL database via Docker."""

    IMAGE = "postgres"
    PORT = 5432
    PASSWORD_ENV_VAR = "POSTGRES_PASSWORD"
    DATA_DIR = "/var/lib/postgresql/data"
    ENGINE_MATCH = "postgresql"
    USER = "postgres"
    DATABASE = "postgres"


class MySQL(DatabaseProvider):
    """Provide a MySQL database via Docker."""

    IMAGE = "mysql"
    PORT = 3306
    PASSWORD_ENV_VAR = "MYSQL_ROOT_PASSWORD"
    CUSTOM_ENV = {"MYSQL_ROOT_HOST": "%"}
    DATA_DIR = "/var/lib/mysql"
    ENGINE_MATCH = "mysql"
    USER = "root"
    DATABASE = "mysql"  # TODO: is this correct?


PROVIDERS = [
    (provider_.ENGINE_MATCH, provider_)
    for provider_ in [
        MySQL,
        PostgreSQL,
    ]
]


def fast_test_database(databases, test_commands=("test",), version=None):
    """
    If running tests, start a database on a tmpfs and set it as the default
    connection.
    """

    if not any(test_command in sys.argv for test_command in test_commands):
        # Not under test, leave connections alone
        return databases

    engine = databases["default"]["ENGINE"]

    match = None
    for engine_match, provider in PROVIDERS:
        if engine_match in engine:
            match = provider
            break

    if not match:
        return databases

    databases = copy(databases)
    databases["default"] = match(version).provide(engine)
    return databases


__all__ = ("fast_test_database",)
