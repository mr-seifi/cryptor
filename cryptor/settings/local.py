from .base import *

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'cryptor_db',
        'USER': 'postgres',
        'PASSWORD': 'postgres'
    }
}

# Redis
REDIS_HOST = '127.0.0.1'
REDIS_PORT = '6379'
