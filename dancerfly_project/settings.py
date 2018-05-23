"""
Django settings for dancerfly_project project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

import os
import dj_database_url

from django.contrib.messages import constants as messages
from django.core.urlresolvers import reverse_lazy

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'NOT_SECRET')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(os.environ.get('DEBUG', True))
USE_DEBUG_TOOLBAR = DEBUG

TEMPLATE_DEBUG = True

ACCEPT_FEEDBACK = True

ALLOWED_HOSTS = []


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
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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
    'brambling.context_processors.current_site',
)

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'brambling.auth_backends.BramblingBackend',
]

if USE_DEBUG_TOOLBAR:
    INSTALLED_APPS += (
        'debug_toolbar.apps.DebugToolbarConfig',
        'template_timings_panel',
    )
    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
        'template_timings_panel.panels.TemplateTimings.TemplateTimings',
    ]

if ACCEPT_FEEDBACK:
    MIDDLEWARE_CLASSES += (
        'talkback.middleware.TalkbackMiddleware',
    )
    INSTALLED_APPS += (
        'talkback',
    )

ROOT_URLCONF = 'dancerfly_project.urls'

WSGI_APPLICATION = 'dancerfly_project.wsgi.application'

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', '')
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', '')
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')

# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config(default="sqlite:///db.sqlite3")
}

# Uncomment to disable migrations temporarily, i.e. for tests
# Source: https://gist.github.com/NotSqrt/5f3c76cd15e40ef62d09
#class DisableMigrations(object):
#
#    def __contains__(self, item):
#        return True
#
#    def __getitem__(self, item):
#        return "notmigrations"
#
#MIGRATION_MODULES = DisableMigrations()

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = os.environ.get('STATIC_URL', '/static/')
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_STORAGE = os.environ.get('STATICFILES_STORAGE', 'django.contrib.staticfiles.storage.StaticFilesStorage')

MEDIA_URL = os.environ.get('MEDIA_URL', '/media/')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
DEFAULT_FILE_STORAGE = os.environ.get('DEFAULT_FILE_STORAGE', 'django.core.files.storage.FileSystemStorage')

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', '')

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = reverse_lazy('login')

AUTH_USER_MODEL = 'brambling.Person'

# These IDs are used for Stripe Connect and Dwolla facilitation
# respectively.
STRIPE_APPLICATION_ID = os.environ.get('STRIPE_APPLICATION_ID', '')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_TEST_APPLICATION_ID = os.environ.get('STRIPE_TEST_APPLICATION_ID', '')
STRIPE_TEST_SECRET_KEY = os.environ.get('STRIPE_TEST_SECRET_KEY', '')
STRIPE_TEST_PUBLISHABLE_KEY = os.environ.get('STRIPE_TEST_PUBLISHABLE_KEY', '')

DWOLLA_APPLICATION_KEY = os.environ.get('DWOLLA_APPLICATION_KEY', '')
DWOLLA_APPLICATION_SECRET = os.environ.get('DWOLLA_APPLICATION_SECRET', '')
DWOLLA_TEST_APPLICATION_KEY = os.environ.get('DWOLLA_TEST_APPLICATION_KEY', '')
DWOLLA_TEST_APPLICATION_SECRET = os.environ.get('DWOLLA_TEST_APPLICATION_SECRET', '')

STRIPE_TEST_ORGANIZATION_ACCESS_TOKEN = os.environ.get('STRIPE_TEST_ORGANIZATION_ACCESS_TOKEN', '')
STRIPE_TEST_ORGANIZATION_PUBLISHABLE_KEY = os.environ.get('STRIPE_TEST_ORGANIZATION_PUBLISHABLE_KEY', '')
STRIPE_TEST_ORGANIZATION_REFRESH_TOKEN = os.environ.get('STRIPE_TEST_ORGANIZATION_REFRESH_TOKEN', '')
STRIPE_TEST_ORGANIZATION_USER_ID = os.environ.get('STRIPE_TEST_ORGANIZATION_USER_ID', '')

DWOLLA_TEST_ORGANIZATION_ACCESS_TOKEN = os.environ.get('DWOLLA_TEST_ORGANIZATION_ACCESS_TOKEN', '')
DWOLLA_TEST_ORGANIZATION_REFRESH_TOKEN = os.environ.get('DWOLLA_TEST_ORGANIZATION_REFRESH_TOKEN', '')
DWOLLA_TEST_ORGANIZATION_USER_ID = os.environ.get('DWOLLA_TEST_ORGANIZATION_USER_ID', '')
DWOLLA_TEST_ORGANIZATION_PIN = os.environ.get('DWOLLA_TEST_ORGANIZATION_PIN', '')
DWOLLA_TEST_USER_ACCESS_TOKEN = os.environ.get('DWOLLA_TEST_USER_ACCESS_TOKEN', '')
DWOLLA_TEST_USER_REFRESH_TOKEN = os.environ.get('DWOLLA_TEST_USER_REFRESH_TOKEN', '')
DWOLLA_TEST_USER_USER_ID = os.environ.get('DWOLLA_TEST_USER_USER_ID', '')
DWOLLA_TEST_USER_PIN = os.environ.get('DWOLLA_TEST_USER_PIN', '')

GRAPPELLI_ADMIN_TITLE = "Dancerfly"

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # other finders..
    'compressor.finders.CompressorFinder',
)

COMPRESS_PRECOMPILERS = (
    ('text/sass', 'django_libsass.SassCompiler'),
)


MESSAGE_TAGS = {
    messages.DEBUG: 'alert alert-info',
    messages.INFO: 'alert alert-info',
    messages.SUCCESS: 'alert alert-success',
    messages.WARNING: 'alert alert-warning',
    messages.ERROR: 'alert alert-danger'
}

try:
    from .local_settings import *  # noqa: F403, F401
except Exception:
    pass
