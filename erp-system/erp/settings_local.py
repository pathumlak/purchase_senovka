"""
Local development settings — override production settings for local use.
Usage: python manage.py runserver --settings=erp.settings_local
"""
from .settings import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']

# Serve media files locally
from django.conf.urls.static import static  # noqa: E402, F401
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'  # noqa: F405

# Show full error pages in browser
TEMPLATES[0]['OPTIONS']['context_processors'] += []  # noqa: F405
