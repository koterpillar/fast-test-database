"""
Django settings for the test project.
"""

from __future__ import print_function

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'secret'

INSTALLED_APPS = ()

MIDDLEWARE_CLASSES = ()

ROOT_URLCONF = 'test_app.urls'

WSGI_APPLICATION = 'test_app.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Print the database configuration for testing
print("--- database configuration ---")
print(json.dumps(DATABASES))
print("--- end database configuration ---")