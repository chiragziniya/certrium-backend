import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify

from common.models import BaseModel
from common.models import MediaProvider
from common.media_storage import ProviderAwareFileField, ProviderAwareImageField


class Employer(BaseModel):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"
        REJECTED = "REJECTED", "Rejected"

    company_name = models.CharField(
        max_length=255
    )

    slug = models.SlugField(
        unique=True
    )

    email = models.EmailField(
        unique=True
    )

    website = models.URLField(
        blank=True,
        null=True
    )

    industry = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    company_size = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    country = models.CharField(
        max_length=100
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    media_provider = models.CharField(
        max_length=20,
        choices=MediaProvider.choices,
        default=MediaProvider.AUTO,
        db_index=True,
        help_text="Where this employer's media (e.g., logo) is stored.",
    )

    logo = ProviderAwareImageField(
        upload_to="employers/logos/",
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )

    is_verified = models.BooleanField(
        default=False
    )

    is_active = models.BooleanField(
        default=True
    )

    onboarding_completed = models.BooleanField(
        default=False
    )

    approved_at = models.DateTimeField(
        blank=True,
        null=True
    )

    notes = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Employer"
        verbose_name_plural = "Employers"
        indexes = [
            models.Index(fields=["status", "is_active"]),
            models.Index(fields=["status", "is_verified"]),
            models.Index(fields=["country", "status"]),
        ]

    @staticmethod
    def _generate_unique_slug(base_slug, instance_pk=None):
        slug = base_slug or uuid.uuid4().hex[:8]
        candidate = slug
        suffix = 2
        queryset = Employer.objects.all()

        if instance_pk:
            queryset = queryset.exclude(pk=instance_pk)

        while queryset.filter(slug=candidate).exists():
            candidate = f"{slug}-{suffix}"
            suffix += 1

        return candidate

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()

        if self.website:
            self.website = self.website.strip()

        if self.company_name:
            self.company_name = self.company_name.strip()

        if not self.slug:
            self.slug = self._generate_unique_slug(slugify(self.company_name), self.pk)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.company_name


class EmployerUser(BaseModel):

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        RECRUITER = "RECRUITER", "Recruiter"
        HR = "HR", "HR"
        VIEWER = "VIEWER", "Viewer"

    employer = models.ForeignKey(
        Employer,
        on_delete=models.CASCADE,
        related_name="users"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employer_memberships"
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.RECRUITER
    )

    is_active = models.BooleanField(
        default=True
    )

    joined_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["employer", "user"],
                name="unique_employer_user_membership",
            )
        ]
        indexes = [
            models.Index(fields=["employer", "role"]),
            models.Index(fields=["employer", "is_active"]),
        ]
        ordering = ["-created_at"]
        verbose_name = "Employer User"
        verbose_name_plural = "Employer Users"

    def __str__(self):
        return f"{self.user.email} - {self.employer.company_name}"


class EmployerVerificationAccess(BaseModel):

    class AccessStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        EXPIRED = "EXPIRED", "Expired"
        REVOKED = "REVOKED", "Revoked"

    employer = models.ForeignKey(
        Employer,
        on_delete=models.CASCADE,
        related_name="verification_accesses"
    )

    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employer_access_requests"
    )

    verification_record = models.ForeignKey(
        "verification.VerificationRecord",
        on_delete=models.CASCADE,
        related_name="employer_accesses"
    )

    access_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    status = models.CharField(
        max_length=20,
        choices=AccessStatus.choices,
        default=AccessStatus.PENDING,
        db_index=True
    )

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="verification_access_requested_by"
    )

    approved_by_candidate = models.BooleanField(
        default=False
    )

    approved_at = models.DateTimeField(
        blank=True,
        null=True
    )

    rejected_at = models.DateTimeField(
        blank=True,
        null=True
    )

    revoked_at = models.DateTimeField(
        blank=True,
        null=True
    )

    expires_at = models.DateTimeField()

    employer_notes = models.TextField(
        blank=True,
        null=True
    )

    candidate_notes = models.TextField(
        blank=True,
        null=True
    )

    access_count = models.PositiveIntegerField(
        default=0
    )

    last_accessed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["employer", "candidate", "verification_record"],
                name="unique_employer_candidate_verification_access",
            )
        ]
        indexes = [
            models.Index(fields=["employer", "status"]),
            models.Index(fields=["candidate", "status"]),
            models.Index(fields=["verification_record", "status"]),
            models.Index(fields=["expires_at"]),
        ]
        ordering = ["-created_at"]
        verbose_name = "Employer Verification Access"
        verbose_name_plural = "Employer Verification Access"

    def __str__(self):
        return f"{self.employer.company_name} - {self.candidate.email}"


class EmployerVerificationReport(BaseModel):

    employer = models.ForeignKey(
        Employer,
        on_delete=models.CASCADE,
        related_name="reports"
    )

    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verification_reports"
    )

    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="generated_verification_reports"
    )

    media_provider = models.CharField(
        max_length=20,
        choices=MediaProvider.choices,
        default=MediaProvider.AUTO,
        db_index=True,
        help_text="Where this report file is stored.",
    )

    report_file = ProviderAwareFileField(
        upload_to="verification/reports/",
        blank=True,
        null=True
    )

    report_name = models.CharField(
        max_length=255
    )

    generated_at = models.DateTimeField(
        auto_now_add=True
    )

    expires_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        indexes = [
            models.Index(fields=["employer", "generated_at"]),
            models.Index(fields=["candidate", "generated_at"]),
            models.Index(fields=["expires_at"]),
        ]
        ordering = ["-created_at"]
        verbose_name = "Employer Verification Report"
        verbose_name_plural = "Employer Verification Reports"

    def __str__(self):
        return self.report_name