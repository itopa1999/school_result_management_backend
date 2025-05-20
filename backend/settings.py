from dotenv import load_dotenv
import os
from datetime import timedelta
from django.utils import timezone

from pathlib import Path

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "templates"


SECRET_KEY = os.environ.get("SECRET_KEY")

DEBUG = os.environ.get("DEBUG") != "False"

ALLOWED_HOSTS = ["*"]


# Application definition

DEFAULT_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

CUSTOM_APPS =[
    'administrator',
    'manager',
    'authentication',
    
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "rest_framework_simplejwt.token_blacklist",
    "rest_framework_simplejwt",
    'drf_yasg',
]

INSTALLED_APPS = DEFAULT_APPS + CUSTOM_APPS + THIRD_PARTY_APPS


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    'corsheaders.middleware.CorsMiddleware',
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"
AUTH_USER_MODEL ='authentication.User'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        'DIRS': [TEMPLATE_DIR],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [

]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "Media")

if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND ='django.core.mail.backends.smtp.EmailBackend'
    
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS') == 'True'
EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')


APPEND_SLASH = False

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Handle HTTPS settings in production
# if not DEBUG:
#     SECURE_SSL_REDIRECT = True  # Force HTTPS in production
#     SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS in production
#     CSRF_COOKIE_SECURE = True  # Ensure CSRF cookie is sent over HTTPS
#     SECURE_HSTS_SECONDS = 31536000  # HTTP Strict Transport Security (HSTS) header to force HTTPS
#     SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#     SECURE_HSTS_PRELOAD = True
# else:
#     SECURE_SSL_REDIRECT = False  # Allow HTTP in development
#     SESSION_COOKIE_SECURE = False  # Allow cookies over HTTP in development
#     CSRF_COOKIE_SECURE = False  # Allow CSRF cookie over HTTP in development
#     SECURE_HSTS_SECONDS = 0  # Disable HSTS in development



CORS_ALLOW_ALL_ORIGINS = True if DEBUG else False
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com"
] if not DEBUG else []



SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=10),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": "",
    "AUDIENCE": None,
    "ISSUER": None,
    "JSON_ENCODER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    # "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_OBTAIN_SERIALIZER": "authentication.serializers.CustomTokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
    "SLIDING_TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer",
    "SLIDING_TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",
}

REST_FRAMEWORK = {
    "NON_FIELD_ERRORS_KEY": "errors",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    "EXCEPTION_HANDLER": "drf_standardized_errors.handler.exception_handler",

}


SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'description': 'JWT Authorization header using the Bearer scheme. Example: "Authorization: Bearer {token}"',
            'name': 'Authorization',
            'in': 'header',
        },
    },
    'USE_SESSION_AUTH': False,
    'PERSIST_AUTH': True,
}

DRF_STANDARDIZED_ERRORS = {
    "ENABLE_IN_DEBUG_FOR_UNHANDLED_EXCEPTIONS": True,
    "EXCEPTION_FORMATTER_CLASS": "backend.exception_formatter.ExceptionFormatter",
}


# ADMINS = [
#     ("Lucky", "luckystarboy01@gmail.com"),
# ]

# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "filters": {
#         "require_debug_false": {
#             "()": "django.utils.log.RequireDebugFalse",
#         },
#         "require_debug_true": {
#             "()": "django.utils.log.RequireDebugTrue",
#         },
#     },
#     "handlers": {
#         "console": {
#             "level": "DEBUG",
#             "class": "logging.StreamHandler",
#             "formatter": "verbose",
#         },
#         "file": {
#             "level": "DEBUG",
#             "class": "logging.FileHandler",
#             "filename": "debug.log",
#             "formatter": "verbose",
#         },
#         "error_file": {
#             "level": "ERROR",
#             "class": "logging.FileHandler",
#             "filename": "errors.log",
#             "formatter": "verbose",
#         },
#         "mail_admins": {
#             "level": "ERROR",
#             "class": "django.utils.log.AdminEmailHandler",
#             "filters": ["require_debug_false"],
#             "email_backend": "django.core.mail.backends.smtp.EmailBackend",
#             "include_html": True,
#         },
#     },
#     "formatters": {
#         "verbose": {
#             "format": "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s",
#             "datefmt": "%Y-%m-%d %H:%M:%S",
#         },
#         "standard": {
#             "format": "[%(asctime)s] [%(levelname)s] %(module)s - %(message)s",
#             "datefmt": "%Y-%m-%d %H:%M:%S",
#         },
#         "json": {  # JSON formatter (optional for structured logging)
#             "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "line": %(lineno)d, "message": "%(message)s"}',
#             "datefmt": "%Y-%m-%dT%H:%M:%S",
#         },
#     },
#     "loggers": {
#         "django": {
#             "handlers": ["file", "mail_admins"],
#             "level": "INFO",
#             "propagate": True,
#         },
#         "django.request": {
#             "handlers": ["console", "error_file"],
#             "level": "ERROR",
#             "propagate": False,
#         },
#     },
# }

PAYSTACK_SECRET_KEY=os.getenv('PAYSTACK_SECRET_KEY')