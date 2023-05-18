"""
Django settings for DropDAPI project.

Generated by 'django-admin startproject' using Django 4.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""
import os
from pathlib import Path
from neomodel import config
import environ
# Initialise environment variables
env = environ.Env()
environ.Env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = [env('ALLOWED_HOSTS')]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'django_neomodel',
    'channels',
    'rest_framework_simplejwt',

    # cutomApps
    'authUser.apps.AuthuserConfig',
    'neoUserModel.apps.NeousermodelConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


CORS_ORIGIN_ALLOW_ALL = True

ROOT_URLCONF = 'DropDAPI.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'DropDAPI.wsgi.application'
ASGI_APPLICATION = 'DropDAPI.asgi.application'
CHANNEL_LAYERS = {
    'default':{
        'BACKEND':'channels_redis.core.RedisChannelLayer',
        'CONFIG':{
            "hosts":[('127.0.0.1',6379)],
        },
    },
}

# REST_FRAMEWORK = {

#     'DEFAULT_AUTHENTICATION_CLASSES': (
#         'rest_framework_simplejwt.authentication.JWTAuthentication',
#     )
# }
# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DATABASE_NAME'),
        'USER': env('DATABASE_USER'),
        'PASSWORD': env('DATABASE_PASSWORD'),
        'HOST': env('DATABASE_HOST'),
        'PORT': env('DATABASE_PORT'),
    }
}

config.DATABASE_URL = env('REMOTE_URL')
config.NEOMODEL_FORCE_TIMEZONE=1

## AWS S3 storage settings

DEFAULT_FILE_STORAGE = env('DEFAULT_FILE_STORAGE')
AWS_S3_ACCESS_KEY_ID = env('AWS_S3_ACCESS_KEY_ID')
AWS_S3_SECRET_ACCESS_KEY = env('AWS_S3_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')

# AWS_S3_ENDPOINT_URL = "arn:aws:s3:ap-southeast-1:502481381794:accesspoint/storage-dropd-network"
# AWS_S3_REGION_NAME  = "ap-southeast-1"

#AWS SES
# EMAIL_BACKEND = 'django_smtp_ssl.SSLEmailBackend'
# EMAIL_HOST = 'email-smtp.ap-southeast-1.amazonaws.com'
# EMAIL_PORT = 465
# EMAIL_HOST_USER ='AKIAXJ7RZNGRNUS5CY5W'
# EMAIL_HOST_PASSWORD ='BAcmC1TPVPC/rfMpsKbjOU/eSI9o+WzzwWZghXcurNJ1'
# EMAIL_USE_SSL = True

###################################
# EMAIL_BACKEND = 'django_ses.SESBackend'
# AWS_ACCESS_KEY_ID = 'AKIAXJ7RZNGRNUS5CY5W'
# AWS_SECRET_ACCESS_KEY = 'BAcmC1TPVPC/rfMpsKbjOU/eSI9o+WzzwWZghXcurNJ1'
# AWS_SES_REGION_NAME = 'ap-southeast-1'
# AWS_SES_REGION_ENDPOINT = 'email-smtp.ap-southeast-1.amazonaws.com'
##################################


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = env('AWS_SES_SMTP_HOST')
EMAIL_PORT = env('AWS_SES_SMTP_PORT')
EMAIL_HOST_USER = env('AWS_SES_SMTP_USER')
EMAIL_HOST_PASSWORD = env('AWS_SES_SMTP_PASSWORD')
EMAIL_USE_TLS = env('AWS_SES_SMTP_TLS')



# EMAIL_HOST = 'smtp.gmail.com'

# EMAIL_PORT = 587

# EMAIL_USE_TLS = True

# EMAIL_HOST_USER = 'django.bot.panda@gmail.com'
# EMAIL_HOST_PASSWORD = 'nfqmzfondbhasted'

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'authUser.Users'

### file upload size 
# FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880

FAKE_IMAGES = os.path.join(BASE_DIR,'fake_images')