"""
Django settings for test_project project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'NOT_SECRET'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
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
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'zenaida',
    'zenaida.contrib.hints',
    'floppyforms',
    'django_filters',
    'daguerre',
    'compressor',
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
)

ROOT_URLCONF = 'test_project.urls'

WSGI_APPLICATION = 'test_project.wsgi.application'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

import os
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')

from django.core.urlresolvers import reverse_lazy

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

STRIPE_TEST_EVENT_ACCESS_TOKEN = os.environ.get('STRIPE_TEST_EVENT_ACCESS_TOKEN', '')
STRIPE_TEST_EVENT_PUBLISHABLE_KEY = os.environ.get('STRIPE_TEST_EVENT_PUBLISHABLE_KEY', '')
STRIPE_TEST_EVENT_REFRESH_TOKEN = os.environ.get('STRIPE_TEST_EVENT_REFRESH_TOKEN', '')
STRIPE_TEST_EVENT_USER_ID = os.environ.get('STRIPE_TEST_EVENT_USER_ID', '')

DWOLLA_TEST_EVENT_ACCESS_TOKEN = os.environ.get('DWOLLA_TEST_EVENT_ACCESS_TOKEN', '')
DWOLLA_TEST_EVENT_USER_ID = os.environ.get('DWOLLA_TEST_EVENT_USER_ID', '')
DWOLLA_TEST_EVENT_PIN = os.environ.get('DWOLLA_TEST_EVENT_PIN', '')
DWOLLA_TEST_USER_ACCESS_TOKEN = os.environ.get('DWOLLA_TEST_USER_ACCESS_TOKEN', '')
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
    ('text/sass', 'sass -r bootstrap-sass --compass "{infile}" {outfile}'),
)


from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'alert alert-info',
    messages.INFO: 'alert alert-info',
    messages.SUCCESS: 'alert alert-success',
    messages.WARNING: 'alert alert-warning',
    messages.ERROR: 'alert alert-danger'
}

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
