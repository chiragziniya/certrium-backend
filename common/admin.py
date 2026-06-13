from django.contrib import admin

try:
	from unfold.admin import ModelAdmin as BaseModelAdmin
except Exception:  # pragma: no cover
	BaseModelAdmin = admin.ModelAdmin
from django.core.cache import cache

from common.media_storage import CONFIG_CACHE_KEY
from common.models import PlatformConfig


@admin.register(PlatformConfig)
class PlatformConfigAdmin(BaseModelAdmin):
	list_display = (
		"default_upload_provider",
		"enable_local",
		"enable_cloudinary",
		"enable_s3",
		"updated_at",
	)

	fieldsets = (
		(
			"Media Storage",
			{
				"fields": (
					"default_upload_provider",
					"enable_local",
					"enable_cloudinary",
					"enable_s3",
					"cloudinary_folder",
					"aws_region",
					"aws_bucket_name",
				)
			},
		),
		(
			"SMTP (non-secret)",
			{
				"fields": (
					"smtp_host",
					"smtp_port",
					"smtp_username",
					"smtp_from_email",
					"smtp_use_tls",
					"smtp_use_ssl",
				)
			},
		),
	)

	def has_add_permission(self, request):
		# Enforce singleton via admin UI.
		if PlatformConfig.objects.exists():
			return False
		return super().has_add_permission(request)

	def save_model(self, request, obj, form, change):
		if request.user and request.user.is_authenticated:
			obj.updated_by = request.user
		super().save_model(request, obj, form, change)
		cache.delete(CONFIG_CACHE_KEY)
