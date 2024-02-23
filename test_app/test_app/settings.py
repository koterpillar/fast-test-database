"""
Django settings for the test project.
"""

import json
import os

from fast_test_database import fast_test_database

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = "secret"

INSTALLED_APPS = ()

MIDDLEWARE_CLASSES = ()

ROOT_URLCONF = "test_app.urls"

WSGI_APPLICATION = "test_app.wsgi.application"

DATABASES = json.loads(os.environ["DATABASES"])

version = None
engine = DATABASES["default"]["ENGINE"]

if "mysql" in engine:
    version = "8.0"
elif "postgresql" in engine:
    version = "15"

DATABASES = fast_test_database(DATABASES, version=version)

# Print the database configuration for testing
print("--- database configuration ---")
print(json.dumps(DATABASES))
print("--- end database configuration ---")
