import uuid

from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        abstract = True


class UUIDModel(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):

    is_deleted = models.BooleanField(
        default=False
    )

    class Meta:
        abstract = True


class BaseModel(
    UUIDModel,
    TimeStampedModel,
    SoftDeleteModel
):

    class Meta:
        abstract = True


class MediaProvider(models.TextChoices):
    AUTO = "AUTO", "Auto (use Platform Config)"
    LOCAL = "LOCAL", "Local"
    CLOUDINARY = "CLOUDINARY", "Cloudinary"
    S3 = "S3", "AWS S3"


class PlatformConfig(BaseModel):
    """Singleton config row for operational toggles.

    Secrets (passwords/API secrets) should live in env vars / secret managers.
    """

    default_upload_provider = models.CharField(
        max_length=20,
        choices=MediaProvider.choices,
        default=MediaProvider.LOCAL,
        db_index=True,
    )

    enable_local = models.BooleanField(default=True)
    enable_cloudinary = models.BooleanField(default=True)
    enable_s3 = models.BooleanField(default=True)

    # Optional: non-secret SMTP config (password in env).
    smtp_host = models.CharField(max_length=255, blank=True, null=True)
    smtp_port = models.PositiveIntegerField(blank=True, null=True)
    smtp_username = models.CharField(max_length=255, blank=True, null=True)
    smtp_from_email = models.EmailField(blank=True, null=True)
    smtp_use_tls = models.BooleanField(default=True)
    smtp_use_ssl = models.BooleanField(default=False)

    # Optional: non-secret provider metadata.
    cloudinary_folder = models.CharField(max_length=255, blank=True, null=True)
    aws_region = models.CharField(max_length=100, blank=True, null=True)
    aws_bucket_name = models.CharField(max_length=255, blank=True, null=True)

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="platform_configs_updated",
    )

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Platform Config"
        verbose_name_plural = "Platform Config"
        indexes = [
            models.Index(fields=["default_upload_provider"]),
        ]

    def __str__(self):
        return "Platform Config"