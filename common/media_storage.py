from __future__ import annotations

import os
import time
from functools import lru_cache

from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import FileSystemStorage, Storage
from django.db import models
from django.db.models.fields.files import FieldFile


CONFIG_CACHE_KEY = "common.platform_config.active.v1"


def _get_platform_config():
    PlatformConfig = apps.get_model("common", "PlatformConfig")
    return PlatformConfig.objects.order_by("-updated_at").first()


def get_platform_config_cached():
    cached = cache.get(CONFIG_CACHE_KEY)
    if cached is not None:
        return cached

    config = _get_platform_config()
    cache.set(CONFIG_CACHE_KEY, config, timeout=60)
    return config


def resolve_default_upload_provider() -> str:
    """Return the provider to use for NEW uploads.

    Uses DB config when available; falls back to env/settings.
    """
    config = get_platform_config_cached()
    if config and getattr(config, "default_upload_provider", None):
        return config.default_upload_provider

    # Fallback: env-driven default.
    return getattr(settings, "DEFAULT_UPLOAD_PROVIDER", "LOCAL")


@lru_cache(maxsize=8)
def _local_storage() -> Storage:
    return FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)


@lru_cache(maxsize=8)
def _s3_storage() -> Storage:
    try:
        from storages.backends.s3boto3 import S3Boto3Storage
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("S3 storage requested but django-storages is not available") from exc

    class CertriumS3MediaStorage(S3Boto3Storage):
        location = "media"

    return CertriumS3MediaStorage()


@lru_cache(maxsize=8)
def _cloudinary_storage() -> Storage:
    try:
        import cloudinary
        import cloudinary.api
        import cloudinary.uploader
        import cloudinary.utils
        from cloudinary_storage.storage import MediaCloudinaryStorage
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Cloudinary storage requested but django-cloudinary-storage is not available"
        ) from exc

    class PrivateCloudinaryStorage(MediaCloudinaryStorage):
        """Stores every asset as Cloudinary 'private' + resource_type='raw'.

        Why raw?
          - Cloudinary strips the extension from the public_id of *image*
            resources, making it impossible to detect the resource type later.
          - 'raw' preserves the full filename (including extension) in the
            public_id, so every subsequent lookup is unambiguous.
          - A document vault never needs Cloudinary image transformations,
            so 'raw' is the semantically correct choice.

        Security:
          - type='private'  → plain URL returns HTTP 401; Cloudinary rejects it.
          - url() returns a signed, time-limited URL (configurable via
            CLOUDINARY_SIGNED_URL_EXPIRY; default 1 hour).
          - DB stores only the public_id – never a live/accessible URL.
        """

        RESOURCE_TYPE = "raw"

        def _get_resource_type(self, name: str) -> str:  # noqa: ARG002
            return "raw"

        def _upload(self, name: str, content) -> dict:
            options = {
                "use_filename": True,
                "unique_filename": False,
                "resource_type": "raw",
                "type": "private",      # ← private delivery
                "tags": self.TAG,
                "overwrite": True,
            }
            folder = os.path.dirname(name)
            if folder:
                options["folder"] = folder
            return cloudinary.uploader.upload(content, **options)

        def _get_url(self, name: str) -> str:
            """Return a signed, time-limited URL for a private Cloudinary asset."""
            name = self._prepend_prefix(name)
            expiry = int(time.time()) + int(
                getattr(settings, "CLOUDINARY_SIGNED_URL_EXPIRY", 3600)
            )
            url, _ = cloudinary.utils.cloudinary_url(
                name,
                resource_type="raw",
                type="private",
                sign_url=True,
                expires_at=expiry,
                secure=True,
            )
            return url

        def url(self, name: str) -> str:
            return self._get_url(name)

        def delete(self, name: str) -> bool:
            """Destroy must specify type='private' or Cloudinary won't locate the asset."""
            response = cloudinary.uploader.destroy(
                name,
                invalidate=True,
                resource_type="raw",
                type="private",
            )
            return response.get("result") == "ok"

        def exists(self, name: str) -> bool:
            """Use the Cloudinary Admin API – HEAD on a private URL is unreliable."""
            try:
                cloudinary.api.resource(
                    self._prepend_prefix(name),
                    resource_type="raw",
                    type="private",
                )
                return True
            except Exception:
                return False

    return PrivateCloudinaryStorage()


def get_storage_for_provider(provider: str) -> Storage:
    provider = (provider or "").upper()

    if provider == "S3":
        return _s3_storage()

    if provider == "CLOUDINARY":
        return _cloudinary_storage()

    return _local_storage()


class ProviderAwareFieldFile(FieldFile):
    """A FieldFile that resolves storage backend based on an instance field."""

    @property
    def storage(self):
        provider_field = getattr(self.field, "provider_field", "media_provider")
        provider = getattr(self.instance, provider_field, None)
        if provider in (None, "", "AUTO"):
            provider = resolve_default_upload_provider()
        return get_storage_for_provider(provider)

    @storage.setter
    def storage(self, value):
        # Django assigns field.storage during init; we intentionally ignore it.
        self._ignored_storage = value


class ProviderAwareFileField(models.FileField):
    """FileField that uses ProviderAwareFieldFile and stamps provider at upload time."""

    attr_class = ProviderAwareFieldFile

    def __init__(self, *args, provider_field: str = "media_provider", **kwargs):
        self.provider_field = provider_field
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.provider_field != "media_provider":
            kwargs["provider_field"] = self.provider_field
        return name, path, args, kwargs

    def pre_save(self, model_instance, add):
        file = getattr(model_instance, self.attname)

        provider = getattr(model_instance, self.provider_field, None)
        if file and provider in (None, "", "AUTO"):
            setattr(model_instance, self.provider_field, resolve_default_upload_provider())

        return super().pre_save(model_instance, add)


class ProviderAwareImageField(models.ImageField):
    """ImageField variant that is provider-aware."""

    attr_class = ProviderAwareFieldFile

    def __init__(self, *args, provider_field: str = "media_provider", **kwargs):
        self.provider_field = provider_field
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.provider_field != "media_provider":
            kwargs["provider_field"] = self.provider_field
        return name, path, args, kwargs

    def pre_save(self, model_instance, add):
        file = getattr(model_instance, self.attname)

        provider = getattr(model_instance, self.provider_field, None)
        if file and provider in (None, "", "AUTO"):
            setattr(model_instance, self.provider_field, resolve_default_upload_provider())

        return super().pre_save(model_instance, add)
