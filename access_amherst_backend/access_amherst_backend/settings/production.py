from .base_settings import *
import dj_database_url

DEBUG = False

DATABASES = {
    'default': dj_database_url.config(default=os.getenv('DATABASE_URL'))
}