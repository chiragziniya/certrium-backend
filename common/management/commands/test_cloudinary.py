"""Smoke-test for *private* Cloudinary uploads.

Usage:
    python manage.py test_cloudinary

Steps:
1. Upload a tiny PNG via the raw SDK with type='private'.
2. Confirm the plain (unsigned) URL returns HTTP 401/403 – i.e. truly private.
3. Generate a signed URL and confirm it returns HTTP 200.
4. Upload via Django's ProviderAwareFileField path (PrivateCloudinaryStorage).
5. Confirm the signed URL from storage.url() is accessible.
6. Delete all test assets.
"""
from __future__ import annotations

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

_ONE_PIXEL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc\xf8\x0f"
    b"\x00\x01\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)
_PUBLIC_ID = "certrium_test/private_smoke_test"


class Command(BaseCommand):
    help = "Upload a tiny test file as PRIVATE to Cloudinary and verify signed-URL access."

    def handle(self, *args, **options):
        import cloudinary
        import cloudinary.uploader
        import cloudinary.utils
        import time

        # ── Step 1: upload as private ────────────────────────────────────
        self.stdout.write("Step 1: uploading as private via raw SDK …")
        try:
            result = cloudinary.uploader.upload(
                _ONE_PIXEL_PNG,
                public_id=_PUBLIC_ID,
                resource_type="image",
                type="private",
                overwrite=True,
            )
            self.stdout.write(self.style.SUCCESS(f"  ✔ public_id: {result['public_id']}"))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"  ✘ Upload failed: {exc}"))
            return

        # ── Step 2: plain URL must NOT be accessible ─────────────────────
        self.stdout.write("Step 2: confirming plain URL is blocked …")
        import cloudinary as _c
        plain_url = (
            f"https://res.cloudinary.com/{_c.config().cloud_name}"
            f"/image/private/{_PUBLIC_ID}.png"
        )
        resp = requests.head(plain_url, timeout=10)
        if resp.status_code in (401, 403):
            self.stdout.write(self.style.SUCCESS(
                f"  ✔ Blocked as expected (HTTP {resp.status_code}) – asset is private."
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"  ⚠ Unexpected status {resp.status_code} for plain URL."
            ))

        # ── Step 3: signed URL must BE accessible ────────────────────────
        self.stdout.write("Step 3: confirming signed URL is accessible …")
        signed_url, _ = cloudinary.utils.cloudinary_url(
            _PUBLIC_ID,
            resource_type="image",
            type="private",
            sign_url=True,
            expires_at=int(time.time()) + 300,
            secure=True,
        )
        resp2 = requests.head(signed_url, timeout=10)
        if resp2.status_code == 200:
            self.stdout.write(self.style.SUCCESS(
                f"  ✔ Signed URL accessible (HTTP 200)."
            ))
            self.stdout.write(f"  URL: {signed_url}")
        else:
            self.stdout.write(self.style.ERROR(
                f"  ✘ Signed URL returned HTTP {resp2.status_code}."
            ))

        # ── Step 4: Django PrivateCloudinaryStorage path ─────────────────
        self.stdout.write("Step 4: uploading via Django PrivateCloudinaryStorage …")
        try:
            from common.media_storage import get_storage_for_provider
            storage = get_storage_for_provider("CLOUDINARY")
            name = storage.save(
                "certrium_test/django_private_test.png",
                ContentFile(_ONE_PIXEL_PNG),
            )
            self.stdout.write(self.style.SUCCESS(f"  ✔ Stored public_id: {name}"))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"  ✘ Django storage upload failed: {exc}"))
            name = None

        # ── Step 5: signed URL from storage.url() ────────────────────────
        if name:
            self.stdout.write("Step 5: verifying signed URL from storage.url() …")
            try:
                dj_url = storage.url(name)
                resp3 = requests.head(dj_url, timeout=10)
                if resp3.status_code == 200:
                    self.stdout.write(self.style.SUCCESS(f"  ✔ Signed URL accessible (HTTP 200)."))
                    self.stdout.write(f"  URL: {dj_url}")
                else:
                    self.stdout.write(self.style.ERROR(
                        f"  ✘ storage.url() returned HTTP {resp3.status_code}."
                    ))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"  ✘ URL check failed: {exc}"))

        # ── Step 6: cleanup ───────────────────────────────────────────────
        self.stdout.write("Step 6: cleaning up test assets …")
        cloudinary.uploader.destroy(_PUBLIC_ID, resource_type="image", type="private")
        self.stdout.write("  ✔ Raw SDK test asset deleted.")
        if name:
            storage.delete(name)
            self.stdout.write("  ✔ Django storage test asset deleted.")

        self.stdout.write(self.style.SUCCESS("\nPrivate Cloudinary smoke test complete."))
