from .base_settings import *

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
    }
}

# For faster test performance, avoid using password validators
AUTH_PASSWORD_VALIDATORS = []