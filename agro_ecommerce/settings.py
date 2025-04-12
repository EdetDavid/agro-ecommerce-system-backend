from datetime import timedelta
from pathlib import Path
import os  # Make sure os is imported if not already

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-j8kdem=sttk+kraz4zp%y-3oh^_j2kc0*+@6$eqsvv^=39m#h("

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".vercel.app",  
    ".now.sh",  
    ".onrender.com"
]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "users",
    "products",
    "orders",
    "payments",
    "reviews",
    "logistics",
    "notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",  # Optional backup
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),  # Adjust as needed
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}


CORS_ORIGIN_ALLOW_ALL = True

ROOT_URLCONF = "agro_ecommerce.urls"

AUTH_USER_MODEL = "users.User"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "agro_ecommerce.wsgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

#  CORS Settings
# CORS_ALLOW_ALL_ORIGINS = False  # More secure than allowing all
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000",  # Default React dev server
#     "http://127.0.0.1:3000",  # Alternative localhost
#     "https://*.vercel.app",  # All Vercel deployments
#     "https://*.now.sh",  # Older Vercel deployments
#     # Add your production frontend URL when ready
# ]

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# Optional: If you need credentials (cookies, auth headers)
CORS_ALLOW_CREDENTIALS = True

# Optional: For fine-grained control over specific paths
CORS_URLS_REGEX = r"^/api/.*$"  # Only allow CORS on API routes

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- PayPal Configuration ---
PAYPAL_MODE = "sandbox"  # Change to "live" for production
# Enforce these as actual environment variables for security

# --- PayPal Configuration ---
PAYPAL_MODE = "sandbox"  # Change to "live" for production
PAYPAL_CLIENT_ID = os.environ.get(
    "AStYh1L52CgAWhblc0kIYsw3xDvjttFuTOaWE2fL6QqpQJhlJ7M058Hsi2xwsbdr_jr9HTvnzRD_97kV",
    "AStYh1L52CgAWhblc0kIYsw3xDvjttFuTOaWE2fL6QqpQJhlJ7M058Hsi2xwsbdr_jr9HTvnzRD_97kV",
)  # Replace with your actual Sandbox Client ID
PAYPAL_CLIENT_SECRET = os.environ.get(
    "EDRFOia1IUgkPO6G0uptEjszRE8mXZmtMbQr4srKJd893iszd5USTOZimvqSq60NnQuzQFfEVUYzujxB",
    "EDRFOia1IUgkPO6G0uptEjszRE8mXZmtMbQr4srKJd893iszd5USTOZimvqSq60NnQuzQFfEVUYzujxB",
)  # Replace with your actual Sandbox Secret


# --- End PayPal Configuration ---
