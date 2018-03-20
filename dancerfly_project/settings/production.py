import os

from .base import *  # noqa: F403, F401

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', '')
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', '')
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')
EMAIL_BACKEND = "sgbackend.SendGridBackend"
