import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET', 'dev-secret-change-me')

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'fees',
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

ROOT_URLCONF = 'fms_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'fees.context_processors.sidebar_context',
            ],
        },
    },
]

# ... existing code ...

SIDEBAR_CONFIG = [
    {
        "title": "Management Console",
        "items": [
            {"label": "Dashboard", "url": "fees:dashboard", "icon": "📊"},
            {"label": "Users", "url": "fees:manage_list", "args": ["customuser"], "icon": "👤"},
            {"label": "Groups", "url": "fees:manage_list", "args": ["group"], "icon": "👥"},
        ]
    },
    {
        "title": "Core Modules",
        "items": [
            {"label": "Students", "url": "fees:manage_list", "args": ["student"], "icon": "🎓"},
            {"label": "Class Fees", "url": "fees:manage_list", "args": ["classfee"], "icon": "🏷️"},
            {"label": "Fee Payments", "url": "fees:manage_list", "args": ["feepayment"], "icon": "💳"},
            {"label": "Fee Records", "url": "fees:manage_list", "args": ["feerecord"], "icon": "📝"},
        ]
    },
    {
        "title": "Financial Reports",
        "items": [
            {"label": "Monthly Summary", "url": "fees:monthly_fees", "icon": "📅"},
            {"label": "Paid Students", "url": "fees:paid_students_list", "icon": "✅"},
            {"label": "Unpaid Students", "url": "fees:unpaid_students_list", "icon": "❌"},
        ]
    },
    {
        "title": "SYSTEM",
        "items": [
            {"label": "Logout", "url": "fees:logout", "icon": "🚪"},
        ]
    }
]

WSGI_APPLICATION = 'fms_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'fees.CustomUser'

SESSION_COOKIE_AGE = 1800  # 30 minutes
SESSION_SAVE_EVERY_REQUEST = True

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
