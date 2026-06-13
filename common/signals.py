from __future__ import annotations

from django.db.models.signals import pre_save
from django.dispatch import receiver

from common.media_storage import (
    ProviderAwareFileField,
    ProviderAwareImageField,
    resolve_default_upload_provider,
)


@receiver(pre_save, dispatch_uid="common.stamp_media_provider.v1")
def stamp_media_provider(sender, instance, **kwargs):
    """Ensure per-record media_provider is persisted for provider-aware fields.

    Why this exists:
    - Field-level `pre_save()` runs while Django is already collecting values for SQL.
    - If the `media_provider` field is evaluated *before* the file field,
      stamping inside the file field `pre_save()` won't persist to DB.

    This signal runs early enough to ensure the provider is saved.
    """

    # Skip raw fixtures.
    if kwargs.get("raw"):
        return

    opts = getattr(instance, "_meta", None)
    if opts is None:
        return

    for field in opts.fields:
        if not isinstance(field, (ProviderAwareFileField, ProviderAwareImageField)):
            continue

        provider_field = getattr(field, "provider_field", "media_provider")
        current_provider = getattr(instance, provider_field, None)
        if current_provider not in (None, "", "AUTO"):
            continue

        file_value = getattr(instance, field.name, None)
        if not file_value:
            continue

        setattr(instance, provider_field, resolve_default_upload_provider())
