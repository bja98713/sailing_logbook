
import os
from pathlib import Path

# Load environment variables from .env file (for deployment)
BASE_DIR = Path(__file__).resolve().parent.parent
env_file = BASE_DIR / '.env'
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key, value)

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes',
    'django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',
    'rest_framework',
    'nautical',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sailing_logbook.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

WSGI_APPLICATION = 'sailing_logbook.wsgi.application'

DATABASES = {'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'db.sqlite3',
}}

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Pacific/Tahiti'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Emplacement du build frontend (Vite) : frontend/build -> static/frontend
FRONTEND_DIR = BASE_DIR / 'static' / 'frontend'
# n'ajouter le dossier frontend que s'il existe (évite l'avertissement W004
# pendant le développement si le build n'a pas encore été exécuté)
if FRONTEND_DIR.exists():
    STATICFILES_DIRS.append(FRONTEND_DIR)

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
