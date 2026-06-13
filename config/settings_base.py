"""Shared Django settings.

Environment-specific overrides live in:
- config.settings_local
- config.settings_staging
- config.settings_production

config.settings selects one of these based on DJANGO_ENV.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import environ
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _


def raw_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def env_int(name: str, default: int) -> int:
    value = raw_env(name)
    if value is None:
        return default
    return int(value)


def env_bool(name: str, default: bool) -> bool:
    value = raw_env(name)
    if value is None:
        return default

    normalized = value.lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    return default


BASE_DIR = Path(__file__).resolve().parent.parent

# Allow choosing a different env file per environment.
# Example: ENV_FILE=.env.local
_env_file_override = os.getenv("ENV_FILE")
_env_file_path = Path(_env_file_override) if _env_file_override else (BASE_DIR / ".env")

env = environ.Env(
    DEBUG=(bool, False),
    TESTING=(bool, False),
    DJANGO_ENV=(str, "local"),
)

if _env_file_path.exists():
    environ.Env.read_env(_env_file_path)

DJANGO_ENV = env("DJANGO_ENV", default="local").lower()


SECRET_KEY = env(
    "SECRET_KEY",
    default="django-insecure-unsafe-default-change-me",
)

DEBUG = env.bool("DEBUG", default=(DJANGO_ENV == "local"))


ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1"],
)


INSTALLED_APPS = [
    # ==========================================
    # UNFOLD ADMIN
    # ==========================================
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "unfold.contrib.import_export",
    "unfold.contrib.guardian",

    # ==========================================
    # DJANGO CORE
    # ==========================================
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # ==========================================
    # THIRD PARTY APPS
    # ==========================================
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "guardian",
    "django_celery_results",
    "django_celery_beat",
    "channels",
    "drf_spectacular",
    "storages",
    "cloudinary",
    "cloudinary_storage",
    "allauth",
    "allauth.account",

    # ==========================================
    # LOCAL APPS
    # ==========================================
    "accounts",
    "institutions",
    "verification",
    "wallets",
    "audit",
    "employers",
    "payments",
    "common.apps.CommonConfig",
]

AUTH_USER_MODEL = "accounts.User"


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",

    "corsheaders.middleware.CorsMiddleware",

    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    # ALLAUTH
    "allauth.account.middleware.AccountMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# =========================================================
# DATABASE (default safe fallback; overridden in staging/prod)
# =========================================================
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{(BASE_DIR / 'db.sqlite3').as_posix()}",
    )
}

if env.bool("TESTING", default=False) or "test" in sys.argv:
    DATABASES["default"] = env.db("TEST_DATABASE_URL", default="sqlite:///:memory:")

DATABASES["default"].setdefault("CONN_MAX_AGE", env_int("DB_CONN_MAX_AGE", default=0))


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
)


LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# =========================================================
# CORS / CSRF
# =========================================================
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=DEBUG)
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = env_bool("CORS_ALLOW_CREDENTIALS", default=True)

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])


# =========================================================
# EMAIL
# =========================================================
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default=(
        "django.core.mail.backends.console.EmailBackend"
        if DEBUG
        else "django.core.mail.backends.smtp.EmailBackend"
    ),
)

EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env_int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", default=False)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@localhost")


# =========================================================
# THIRD-PARTY AUTH (AllAuth)
# =========================================================
SITE_ID = 1
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = env("ACCOUNT_EMAIL_VERIFICATION", default="optional")

LOGIN_REDIRECT_URL = "/admin/"
LOGOUT_REDIRECT_URL = "/admin/login/"


def environment_callback(request):
    if request.user.is_superuser:
        return ["Super Admin", "danger"]
    return ["Vaultix", "info"]


# =========================================================
# UNFOLD ADMIN
# =========================================================
UNFOLD = {
    "SITE_TITLE": "Vaultix Admin",
    "SITE_HEADER": "Vaultix",
    "SITE_SUBHEADER": "Trust Verification Infrastructure",
    "SITE_ICON": {
        "light": lambda request: static("images/logo-light.png"),
        "dark": lambda request: static("images/logo-dark.png"),
    },
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/svg+xml",
            "href": lambda request: static("favicon.svg"),
        }
    ],
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "SHOW_BACK_BUTTON": True,
    "SHOW_UI_WARNINGS": False,
    "ENVIRONMENT": "config.settings.environment_callback",
    "THEME": None,
    "BORDER_RADIUS": "10px",
    "LOGIN": {
        "image": lambda request: static("images/login-bg.jpg"),
        "redirect_after": lambda request: reverse_lazy("admin:index"),
    },
    "STYLES": [lambda request: static("css/admin.css")],
    "SCRIPTS": [lambda request: static("js/admin.js")],
    "COLORS": {
        "primary": {
            "50": "255 241 242",
            "100": "255 228 230",
            "200": "254 205 211",
            "300": "253 164 175",
            "400": "251 113 133",
            "500": "244 63 94",
            "600": "225 29 72",
            "700": "190 24 74",
            "800": "159 18 57",
            "900": "136 19 55",
            "950": "76 5 25",
        },
        "base": {
            "50": "249 250 251",
            "100": "243 244 246",
            "200": "229 231 235",
            "300": "209 213 219",
            "400": "156 163 175",
            "500": "75 85 99",
            "600": "55 65 81",
            "700": "43 43 43",
            "800": "31 31 31",
            "900": "24 24 24",
            "950": "14 14 14",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "command_search": True,
        "show_app_list": True,
        "navigation": [
            {
                "title": _("\nDashboard"),
                "separator": True,
                "collapsible": False,
                "items": [
                    {
                        "title": _("Overview"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": _("User Management"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "group",
                        "link": reverse_lazy("admin:accounts_user_changelist"),
                    },
                    {
                        "title": _("Institutions"),
                        "icon": "school",
                        "link": reverse_lazy(
                            "admin:institutions_institution_changelist"
                        ),
                    },
                    {
                        "title": _("Institution Requests"),
                        "icon": "domain_add",
                        "link": reverse_lazy(
                            "admin:institutions_institutionrequest_changelist"
                        ),
                    },
                    {
                        "title": _("Employers"),
                        "icon": "business",
                        "link": reverse_lazy("admin:employers_employer_changelist"),
                    },
                ],
            },
            {
                "title": _("Verification"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Verification Records"),
                        "icon": "verified",
                        "link": reverse_lazy(
                            "admin:verification_verificationrecord_changelist"
                        ),
                    },
                    {
                        "title": _("Credential Documents"),
                        "icon": "description",
                        "link": reverse_lazy(
                            "admin:verification_credentialdocument_changelist"
                        ),
                    },
                    {
                        "title": _("Verification Events"),
                        "icon": "history",
                        "link": reverse_lazy(
                            "admin:verification_verificationevent_changelist"
                        ),
                    },
                ],
            },
            {
                "title": _("Wallets"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Wallets"),
                        "icon": "account_balance_wallet",
                        "link": reverse_lazy("admin:wallets_wallet_changelist"),
                    },
                    {
                        "title": _("Wallet Records"),
                        "icon": "badge",
                        "link": reverse_lazy(
                            "admin:wallets_walletrecord_changelist"
                        ),
                    },
                    {
                        "title": _("Wallet Shares"),
                        "icon": "share",
                        "link": reverse_lazy("admin:wallets_walletshare_changelist"),
                    },
                ],
            },
            {
                "title": _("Payments"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Transactions"),
                        "icon": "payments",
                        "link": reverse_lazy(
                            "admin:payments_paymenttransaction_changelist"
                        ),
                    },
                    {
                        "title": _("Invoices"),
                        "icon": "receipt_long",
                        "link": reverse_lazy("admin:payments_invoice_changelist"),
                    },
                    {
                        "title": _("Subscriptions"),
                        "icon": "workspace_premium",
                        "link": reverse_lazy(
                            "admin:payments_usersubscription_changelist"
                        ),
                    },
                ],
            },
            {
                "title": _("Audit & Security"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Audit Logs"),
                        "icon": "policy",
                        "link": reverse_lazy("admin:audit_auditlog_changelist"),
                    },
                    {
                        "title": _("Security Events"),
                        "icon": "security",
                        "link": reverse_lazy(
                            "admin:audit_securityevent_changelist"
                        ),
                    },
                    {
                        "title": _("Activity Timeline"),
                        "icon": "timeline",
                        "link": reverse_lazy(
                            "admin:audit_activitytimeline_changelist"
                        ),
                    },
                ],
            },
            {
                "title": _("System"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Groups"),
                        "icon": "admin_panel_settings",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                    {
                        "title": _("Celery Tasks"),
                        "icon": "schedule",
                        "link": reverse_lazy(
                            "admin:django_celery_beat_periodictask_changelist"
                        ),
                    },
                ],
            },
        ],
    },
}


# =========================================================
# MEDIA STORAGE (ENV-DRIVEN SECRETS)
# =========================================================
DEFAULT_UPLOAD_PROVIDER = env("DEFAULT_UPLOAD_PROVIDER", default="LOCAL").upper()

# Cloudinary
CLOUDINARY_URL = env("CLOUDINARY_URL", default=None)
# How long (seconds) a signed private Cloudinary URL is valid. Default: 1 hour.
CLOUDINARY_SIGNED_URL_EXPIRY = env_int("CLOUDINARY_SIGNED_URL_EXPIRY", default=3600)

if CLOUDINARY_URL:
    import re as _re
    _m = _re.match(
        r"cloudinary://(?P<key>[^:]+):(?P<secret>[^@]+)@(?P<cloud>.+)",
        CLOUDINARY_URL,
    )
    if _m:
        import cloudinary as _cloudinary
        _cloudinary.config(
            cloud_name=_m.group("cloud"),
            api_key=_m.group("key"),
            api_secret=_m.group("secret"),
            secure=True,
        )
        CLOUDINARY_STORAGE = {
            "CLOUD_NAME": _m.group("cloud"),
            "API_KEY": _m.group("key"),
            "API_SECRET": _m.group("secret"),
        }

# AWS S3
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default=None)
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default=None)
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default=None)
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default=None)
AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default=None)
AWS_DEFAULT_ACL = env("AWS_DEFAULT_ACL", default=None)
AWS_QUERYSTRING_AUTH = env_bool("AWS_QUERYSTRING_AUTH", default=True)
