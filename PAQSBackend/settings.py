
from pathlib import Path
import os
import datetime
import re
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [ '127.0.0.1', 'localhost', 'web-production-ef21.up.railway.app']

SITE_ID = 1

# Application definition

INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'rest_framework.authtoken',
    'rest_auth',
    'corsheaders',
    'drf_yasg',
    'accounts',
    'payments',
    'product',
    'social_auth',
    'entry',
    'csp',
    'storages'
]


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
     "csp.middleware.CSPMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
REDIS_URL = f"redis://{os.environ.get('REDISUSER', default='default')}:{os.environ.get('REDISPASSWORD', default='')}@{os.environ.get('REDISHOST', default='redis')}:{os.environ.get('REDISPORT', default=6379)}"

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", default="django-db")
CELERY_BEAT_SCHEDULER = os.environ.get(
    "CELERY_BEAT_SCHEDULER", default="django_celery_beat.schedulers.DatabaseScheduler"
)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERYD_HIJACK_ROOT_LOGGER = False

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(os.environ.get("CHANNELS_URLS", "redis://localhost:6379/0"))],
        },
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

ROOT_URLCONF = 'PAQSBackend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # BASE_DIR / "email-templates/src/templates",
            # BASE_DIR / "email-templates/build_production",
            BASE_DIR / "templates",
            # BASE_DIR / "new-template-directory", 
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'PAQSBackend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
       'ENGINE': 'django.db.backends.postgresql_psycopg2',
       'DATABASE_URL': os.getenv("DB_URL"),
       'NAME': os.getenv("DB_NAME"),
       'USER': os.getenv("DB_USER"),
       'PASSWORD': os.getenv("DB_PASSWORD"),
       'HOST': os.getenv("DB_HOST"),
       'PORT': os.getenv("DB_PORT"),
       "CONN_MAX_AGE": 60,
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_build', 'static')
MEDIA_URL = "/images/"
MEDIA_ROOT = os.path.join(BASE_DIR, "static/images/paqs")
STATICFILES_DIRS = [
    os.path.join(
        BASE_DIR,
        "static",
    ),
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOWED_ORIGINS = [
    'https://company-six-liard.vercel.app', #company temporal
    'https://users-rouge.vercel.app', #user temporal
    "https://web-production-ef21.up.railway.app", # backend url
    "http://localhost:8080",
    "http://localhost:7200",
    "http://localhost:9000",
    "http://localhost:9200",
    "http://localhost:9201",
    "http://localhost:9202",
    "http://127.0.0.1:9000",
    "https://paqs-l46fiysct-osahenes-projects.vercel.app",
    "https://vercel.com",
]

CSRF_COOKIE_SECURE = True
CSRF_HEADER_NAME = "X_CSRFToken"

SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = False
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:7200/", 'https://*.ngrok.io', 'https://web-production-ef21.up.railway.app'
]

CORS_ALLOW_HEADERS = [
    "access-control-allow-origin",
    "authorization",
    "content-type",
    "withcredentials",
]


AUTHENTICATION_BACKENDS = [
    'accounts.base.CustomUserCompanyAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]


AUTH_USER_MODEL = "accounts.AbstractUserProfile"

import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
)


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY")
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
SOCIAL_AUTH_PASSWORD = os.getenv('SOCIAL_AUTH_PASSWORD')

AWS_ACCESS_KEY_ID = os.getenv("ACCESS_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("BUCKET_NAME")
AWS_S3_REGION_NAME = os.getenv("BUCKET_LOCATION")
AWS_S3_SIGNATURE_NAME = os.getenv("SIGNATURE")
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL =  None
AWS_S3_VERITY = True
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'



CONTENT_SECURITY_POLICY = {
    "EXCLUDE_URL_PREFIXES": ["/excluded-path/"],
    "DIRECTIVES": {
        "default-src": ["'self'", "https://web-production-ef21.up.railway.app"],
        "script-src": ["'self'", "'unsafe-eval'"  "https://web-production-ef21.up.railway.app", "'blob:'"],
        "style-src": ["'self'"],
        "connect-src": ["'self'", "https://web-production-ef21.up.railway.app"],
        "font-src": ["'self'"],
        "object-src": ["'none'"],
        "frame-ancestors": ["'self'"],
        "form-action": ["'self'"],
        "base-uri": ["'self'"],
        "report-uri": "/csp-report/",
        "upgrade-insecure-requests": True,
    },
}

CONTENT_SECURITY_POLICY_REPORT_ONLY = {
    "EXCLUDE_URL_PREFIXES": ["/excluded-path/"],
    "DIRECTIVES": {
        "default-src": ["'none'"],
        "connect-src": ["'self'"],
        "img-src": ["'self'"],
        "form-action": ["'self'"],
        "frame-ancestors": ["'self'"],
        "script-src": ["'self'"],
        "style-src": ["'self'"],
        "upgrade-insecure-requests": True,
        "report-uri": "/csp-report/",
    },
}


IGNORABLE_404_URLS = [
    re.compile(r"^/apple-touch-icon.*\.png$"),
    re.compile(r"^/favicon\.ico$"),
    re.compile(r"^/robots\.txt$"),
]

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'NON_FIELD_ERRORS_KEY': 'error',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # 'DEFAULT_PERMISSION_CLASSES': ( 'rest_framework.permissions.IsAdminUser', 
    #                                'rest_framework.permissions.IsAuthenticated',
    #                                ),
}



SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': datetime.timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': datetime.timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JSON_ENCODER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': datetime.timedelta(minutes=40),
    'SLIDING_TOKEN_REFRESH_LIFETIME': datetime.timedelta(days=1),
}

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    }
}

