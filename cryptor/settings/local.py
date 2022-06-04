from .base import *

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3')
    }
}

# Redis
REDIS_HOST = '127.0.0.1'
REDIS_PORT = '6379'

# Sentry
sentry_sdk.init(
    dsn="https://178c5601316f40ca997bd2a427af7651@o1274582.ingest.sentry.io/6469721",
    integrations=[DjangoIntegration()],

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,

    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True,
    debug=True
)
