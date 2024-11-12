import os

ENVIRONMENT = os.getenv("DJANGO_ENV", "production")

if ENVIRONMENT == "testing":
    from .testing import *
else:
    from .production import *