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

import os
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')

from django.core.urlresolvers import reverse_lazy

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = reverse_lazy('login')

AUTH_USER_MODEL = 'brambling.Person'

# These IDs are used for Stripe Connect and Dwolla facilitation
# respectively.
STRIPE_APPLICATION_ID = 'ca_4chE5N2oG6pt6DiuYQH72YlP9NMNyeue'
STRIPE_SECRET_KEY = 'sk_live_cOzWsg6CPNOL1NNsSSH5diQ7'
STRIPE_PUBLISHABLE_KEY = 'pk_live_XKQYbmGvypJzmCyDYxYGdPpw'
STRIPE_TEST_APPLICATION_ID = 'ca_4chEaXTzoWf7wlHdukG9gYj2n4ivgvpR'
STRIPE_TEST_SECRET_KEY = 'sk_test_cJmntbAoZ16vkdpxGn7ER42K'
STRIPE_TEST_PUBLISHABLE_KEY = 'pk_test_ydOdmGwlFxH8RAQamI3bl7uN'

DWOLLA_APPLICATION_KEY = 'wcbiZAojyXnVOhXcUyB1rhorAlQHXsoSl2rLUiQ+wsyiWsfOCb'
DWOLLA_APPLICATION_SECRET = 'UmFrMeg05htMr8KGI3vbQxPEQ/CgIU+R8GOChkj2VnK+QuBYHS'
DWOLLA_TEST_APPLICATION_KEY = 'jDSD1iaol9g5q5v3xlQZpFR7mAC3KZliGDMe0SUj1w88JlKn5a'
DWOLLA_TEST_APPLICATION_SECRET = 'HdzUEIHaDD4zd1auCsb/wsyLaiva7e6X8+IJpRQqDviM+YLHDm'

STRIPE_TEST_EVENT_ACCESS_TOKEN = 'sk_test_wZYrMs2UqyIbpeHVoFwUxWIa'
STRIPE_TEST_EVENT_PUBLISHABLE_KEY = 'pk_test_zyQ7JNz67DvMBL6rVZFPiDiK'
STRIPE_TEST_EVENT_REFRESH_TOKEN = 'rt_4cuhErVz7FZIyws8N6lUYXem93mTPdZhJTLuvRH33YA5PJ8l'
STRIPE_TEST_EVENT_USER_ID = 'acct_103ulr2dPuL5A6oo'

DWOLLA_TEST_EVENT_ACCESS_TOKEN = 'jMI+S4MoikmNPOOnSTUPF9qAND5quEhIh4ZJVHSa2NtHODZHa8'
DWOLLA_TEST_EVENT_USER_ID = '812-158-1368'
DWOLLA_TEST_EVENT_PIN = '4093'
DWOLLA_TEST_USER_ACCESS_TOKEN = 'Y/C6FBXPqDz9Ixmg3p8d6cmraAB+5/yPKpb3sqBgW0KVLeQ91w'
DWOLLA_TEST_USER_USER_ID = '812-743-0925'
DWOLLA_TEST_USER_PIN = '1234'

GRAPPELLI_ADMIN_TITLE = "Dancerfly"


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
        'zenaida.contrib.feedback.middleware.FeedbackMiddleware',
    )
    INSTALLED_APPS += (
        'zenaida.contrib.feedback',
    )
