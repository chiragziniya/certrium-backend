"""Production settings.

Stricter defaults than staging.
"""

from __future__ import annotations

from .settings_base import *  # noqa

DJANGO_ENV = "production"
DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])  # noqa: F405

DATABASES = {"default": env.db("DATABASE_URL")}  # noqa: F405
DATABASES["default"].setdefault("CONN_MAX_AGE", env_int("DB_CONN_MAX_AGE", default=120))  # noqa: F405

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", default=True)

SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", default=True)
SECURE_REFERRER_POLICY = env("SECURE_REFERRER_POLICY", default="same-origin")

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405
CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", default=False)  # noqa: F405
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])  # noqa: F405
