"""
Fast test database - main module.
"""

import sys


def fast_test_database(databases):
    """
    If running tests, start a database on a tmpfs and set it as the default
    connection.
    """

    test_commands = ('test',)

    if not any(test_command in sys.argv for test_command in test_commands):
        # Not under test, leave connections alone
        return databases

    raise NotImplementedError
