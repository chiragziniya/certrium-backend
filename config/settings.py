"""Environment loader.

Keep `DJANGO_SETTINGS_MODULE=config.settings` everywhere.

Select the environment using `DJANGO_ENV`:
- local
- staging
- production

Optional: set `ENV_FILE` to choose a different env file, e.g. `.env.local`.
"""

from __future__ import annotations

import os
from pathlib import Path

import environ


BASE_DIR = Path(__file__).resolve().parent.parent

_env_file_override = os.getenv("ENV_FILE")
_env_file_path = Path(_env_file_override) if _env_file_override else (BASE_DIR / ".env")

if _env_file_path.exists():
    environ.Env.read_env(_env_file_path)

_env = os.getenv("DJANGO_ENV", "local").lower().strip()

if _env in {"prod", "production"}:
    from .settings_production import *  # noqa
elif _env in {"stage", "staging"}:
    from .settings_staging import *  # noqa
else:
    from .settings_local import *  # noqa