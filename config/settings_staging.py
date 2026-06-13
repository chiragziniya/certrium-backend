"""Staging settings.

Keep secrets in env vars / deployment secret store.
"""

from __future__ import annotations

from .settings_base import *  # noqa

DJANGO_ENV = "staging"
DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])  # noqa: F405

# Require DATABASE_URL in staging.
DATABASES = {"default": env.db("DATABASE_URL")}  # noqa: F405
DATABASES["default"].setdefault("CONN_MAX_AGE", env_int("DB_CONN_MAX_AGE", default=60))  # noqa: F405

# Typical reverse-proxy SSL setup.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", default=True)

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405
CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", default=False)  # noqa: F405
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])  # noqa: F405
