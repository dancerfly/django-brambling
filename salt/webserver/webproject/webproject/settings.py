"""
Django settings for webproject project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


ADMINS = (
    ('Dancerfly Support', 'support@dancerfly.com'),
)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '{{ pillar["deploy"]["secret_key"] }}'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = {% if pillar['deploy']['debug'] %}True{% else %}False{% endif %}

TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = (
    'brambling',
    'grappelli',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'zenaida',
    'zenaida.contrib.hints',
    'talkback',
    'floppyforms',
    'django_filters',
    'daguerre',
    'compressor',
    'rest_framework',
    'bootstrap',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'talkback.middleware.TalkbackMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
    "brambling.context_processors.google_analytics",
    'brambling.context_processors.current_site',
)

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'brambling.auth_backends.BramblingBackend',
]

ROOT_URLCONF = 'webproject.urls'

WSGI_APPLICATION = 'webproject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '{{ pillar["connections"]["db"]["name"] }}',
        'USER': '{{ pillar["connections"]["db"]["user"] }}',
        'PASSWORD': '{{ pillar["connections"]["db"]["password"] }}',
        'HOST': '{{ pillar["connections"]["db"]["host"] }}',
        'PORT': '{{ pillar["connections"]["db"]["port"] }}',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Media files (Uploaded)
MEDIA_ROOT = '{{ pillar["files"]["media_dir"] }}'
MEDIA_URL = '/media/'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/
STATIC_ROOT = '{{ pillar["files"]["static_dir"] }}'
STATIC_URL = '/static/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # other finders..
    'compressor.finders.CompressorFinder',
)

COMPRESS_PRECOMPILERS = (
    ('text/sass', 'django_libsass.SassCompiler'),
)

from django.core.urlresolvers import reverse_lazy

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = reverse_lazy('login')

AUTH_USER_MODEL = 'brambling.Person'

STRIPE_APPLICATION_ID = '{{ pillar["deploy"]["stripe_application_id"] }}'
STRIPE_PUBLISHABLE_KEY = '{{ pillar["deploy"]["stripe_pk"] }}'
STRIPE_SECRET_KEY = '{{ pillar["deploy"]["stripe_sk"] }}'
STRIPE_TEST_APPLICATION_ID = '{{ pillar["deploy"]["stripe_test_application_id"] }}'
STRIPE_TEST_PUBLISHABLE_KEY = '{{ pillar["deploy"]["stripe_test_pk"] }}'
STRIPE_TEST_SECRET_KEY = '{{ pillar["deploy"]["stripe_test_sk"] }}'

DWOLLA_APPLICATION_KEY = '{{ pillar["deploy"]["dwolla_application_key"] }}'
DWOLLA_APPLICATION_SECRET = '{{ pillar["deploy"]["dwolla_application_secret"] }}'
DWOLLA_TEST_APPLICATION_KEY = '{{ pillar["deploy"]["dwolla_test_application_key"] }}'
DWOLLA_TEST_APPLICATION_SECRET = '{{ pillar["deploy"]["dwolla_test_application_secret"] }}'

DEFAULT_FROM_EMAIL = '{{ pillar["deploy"]["default_from_email"] }}'
SERVER_EMAIL = '{{ pillar["deploy"]["server_email"] }}'
SENDGRID_API_KEY = '{{ pillar["deploy"]["sendgrid_api_key"] }}'
EMAIL_BACKEND = "sgbackend.SendGridBackend"

GOOGLE_ANALYTICS_UA = 'UA-52154832-1'
GOOGLE_ANALYTICS_DOMAIN = 'dancerfly.com'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s %(levelname)s] %(message)s",
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '{{ pillar["files"]["logs"]["django_file"] }}',
            # Max size: 2MB
            'maxBytes': 2 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
    },
    'loggers': {
        'brambling': {
            'handlers': ['file', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['file', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['file', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
