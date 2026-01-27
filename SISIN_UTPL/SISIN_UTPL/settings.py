import os
import dj_database_url
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- CONFIGURACIÓN DE SEGURIDAD PARA DESPLIEGUE ---
# Render nos dará una SECRET_KEY, si no, usa la que ya tenías por defecto
SECRET_KEY = os.environ.get('SECRET_KEY', "django-insecure-6npi*(29#@=0z40%(2w9#bbb-05(=!zsaj2nc9tilf62tp&*f9")

# DEBUG será False en Render (porque pondremos la variable DEBUG=False allá)
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Permitimos todos los hosts en Render
ALLOWED_HOSTS = ['*']

# --- DEFINICIÓN DE APLICACIONES ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_fsm",
    # Apps del proyecto
    "usuarios",
    "polizas",
    "siniestros",
    "notificaciones",
    "reportes",
    "gerencia",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware", # <-- Agregado para archivos estáticos
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "SISIN_UTPL.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "SISIN_UTPL.wsgi.application"

# --- BASE DE DATOS DINÁMICA ---
# Si detecta DATABASE_URL (en Render), la usa. Si no, usa tu configuración local de Postgres.
DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://postgres:password@localhost:5432/sisis_utpl',
        conn_max_age=600
    )
}

# --- VALIDACIÓN DE PASSWORDS ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- INTERNACIONALIZACIÓN ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- ARCHIVOS ESTÁTICOS Y MEDIA (CONFIGURACIÓN PARA RENDER) ---
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles" # Carpeta donde se reunirán los estáticos al desplegar

# Esto permite que WhiteNoise comprima los archivos para que carguen rápido
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- CONFIGURACIÓN DE EMAIL (TUS CREDENCIALES) ---
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "cris235g.1@gmail.com"
EMAIL_HOST_PASSWORD = "gchm fnsj jzad urim" 
DEFAULT_FROM_EMAIL = 'SISIN UTPL <cris235g.1@gmail.com>'
SERVER_EMAIL = 'cris235g.1@gmail.com'

# --- REDIRECCIONES ---
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'redireccion_inicial'
LOGOUT_REDIRECT_URL = 'login'