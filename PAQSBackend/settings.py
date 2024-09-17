
from pathlib import Path
import os
import datetime
import re
from dotenv import load_dotenv
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# Load keys from environment
PRIVATE_KEY = str(os.environ.get('PRIVATE_KEY')).replace('\\n', '\n')
PUBLIC_KEY = str(os.environ.get('PUBLIC_KEY')).replace('\\n', '\n')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [ '127.0.0.1', 'localhost','paqs.vercel.app' , 'paqscompany.vercel.app', 'paqsbackend.up.railway.app']

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
    'django_celery_beat',
    'django_celery_results',
    # 'django_mongoengine',
    # 'django_mongoengine.admin',
    # 'django_weasyprint',
    'django_ratelimit',
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

REDIS_URL = os.environ.get("REDIS_CONNECT")

CELERY_BROKER_URL =  REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
# CELERY CONFIG
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND")
CELERY_BEAT_SCHEDULER = os.environ.get("CELERY_BEAT_SCHEDULER")
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# REDIS CACHE CONFIG
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    },
    "ratelimit": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    },
}
RATELIMIT_USE_CACHE = 'ratelimit'

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
    'default': dj_database_url.parse(os.getenv('PGCONNECT')),
    'heavy': dj_database_url.parse(os.getenv('PGCONNECT2')),
}

DATABASE_ROUTERS = ['PAQSBackend.db_router.PartitionRouter']

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

import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {  
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'botocore': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'boto3': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        's3transfer': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'urllib3': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
DEFAULT_FROM_EMAIL = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY")
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
SOCIAL_AUTH_PASSWORD = os.getenv('SOCIAL_AUTH_PASSWORD')

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE")
TWILIO_CHANNEL = os.environ.get("TWILIO_CHANNEL")

AWS_ACCESS_KEY_ID = os.getenv("ACCESS_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("BUCKET_NAME")
AWS_S3_REGION_NAME = os.getenv("BUCKET_LOCATION")
AWS_S3_SIGNATURE_NAME = os.getenv("SIGNATURE")
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL =  None
AWS_S3_VERITY = True
AWS_LOCATION = 'static'
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_build', 'static')
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, "static/images/paqs")
STATICFILES_DIRS = [
    os.path.join(
        BASE_DIR,
        "static",
    ),
]
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOWED_ORIGINS = [
    'https://paqscompany.vercel.app', #company temporal
    'https://paqs.vercel.app', #user temporal
    "https://paqsbackend.up.railway.app", # backend url
    "https://vercel.com",
    'http://127.0.0.1:8000',
    'http://localhost:9000'
]
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
CSRF_HEADER_NAME = "X_CSRFToken"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTOCOL", "https")
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 31536000  
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
CORS_ALLOW_CREDENTIALS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
CSRF_TRUSTED_ORIGINS = [
    'https://paqsbackend.up.railway.app', 
    'https://paqscompany.vercel.app',
    'https://paqs.vercel.app'
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

# CSP_DEFAULT_SRC = ("'self'", "*")
# CSP_SCRIPT_SRC = ("'self'", "*", "'unsafe-inline'", "'unsafe-eval'")
# CSP_STYLE_SRC = ("'self'", "*", "'unsafe-inline'")
# CSP_IMG_SRC = ("'self'", "*")
# CSP_FONT_SRC = ("'self'", "*")

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": [
            "'self'", 
            "https://paqsbackend.up.railway.app", 
            "https://paqsstoragebucket.s3.amazonaws.com"
        ],
        "script-src": [
            "'self'", 
            "'unsafe-eval'",  
            "https://paqsbackend.up.railway.app", 
            "https://paqsstoragebucket.s3.amazonaws.com", 
            "https://paqscompany.vercel.app", 
            "'blob:'"
        ],
        "script-src-elem": [
            "'self'", 
            "'unsafe-eval'", 
            "https://paqsbackend.up.railway.app", 
            "https://paqsstoragebucket.s3.amazonaws.com", 
            "https://paqscompany.vercel.app"
        ],
        "style-src": [
            "'self'", 
            "https://paqscompany.vercel.app", 
            "https://paqsstoragebucket.s3.amazonaws.com", 
            "'unsafe-inline'"  # allows inline CSS, useful if you have inline styles
        ],
        "style-src-elem": [
            "'self'", 
            "https://paqscompany.vercel.app", 
            "https://paqsstoragebucket.s3.amazonaws.com", 
            "'unsafe-inline'"
        ],
        "connect-src": [
            "'self'", 
            "https://paqsbackend.up.railway.app", 
            "https://paqs.vercel.app", 
            "https://paqscompany.vercel.app", 
            "https://paqsstoragebucket.s3.amazonaws.com"
        ],
        "img-src": [
            "'self'", 
            "blob:", 
            "data:", 
            "https://paqsbackend.up.railway.app", 
            "https://paqsstoragebucket.s3.amazonaws.com"
        ],
        "font-src": [
            "'self'", 
            "https://paqsstoragebucket.s3.amazonaws.com"
        ],
        "object-src": ["'none'"],
        "frame-ancestors": ["'self'"],
        "form-action": ["'self'"],
        "base-uri": ["'self'"],
        "report-uri": "https://paqscompany.vercel.app/account/csp-report/",
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
}



SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': datetime.timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': datetime.timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JSON_ENCODER': None,
    'JWK_URL': None,
    'LEEWAY': datetime.timedelta(seconds=30),

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
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

