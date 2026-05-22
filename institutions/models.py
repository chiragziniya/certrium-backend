import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify

from common.models import BaseModel


class Institution(BaseModel):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        SUSPENDED = "SUSPENDED", "Suspended"

    name = models.CharField(
        max_length=255
    )

    slug = models.SlugField(
        unique=True,
        blank=True
    )

    email = models.EmailField(
        unique=True
    )

    website = models.URLField(
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

    description = models.TextField(
        blank=True,
        null=True
    )

    logo = models.ImageField(
        upload_to="institutions/logos/",
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )

    is_active = models.BooleanField(
        default=True
    )

    is_verified = models.BooleanField(
        default=False
    )

    onboarding_completed = models.BooleanField(
        default=False
    )

    verification_email_sent = models.BooleanField(
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

    notes = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Institution"
        verbose_name_plural = "Institutions"
        indexes = [
            models.Index(fields=["status", "is_active"]),
            models.Index(fields=["status", "is_verified"]),
        ]

    @staticmethod
    def _generate_unique_slug(base_slug, instance_pk=None):
        slug = base_slug or uuid.uuid4().hex[:8]
        candidate = slug
        suffix = 2
        queryset = Institution.objects.all()

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

        if self.name:
            self.name = self.name.strip()

        if not self.slug:
            self.slug = self._generate_unique_slug(slugify(self.name), self.pk)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class InstitutionDomain(BaseModel):

    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="domains"
    )

    domain = models.CharField(
        max_length=255,
        unique=True
    )

    is_verified = models.BooleanField(
        default=False
    )

    verification_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    verified_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["domain"]
        verbose_name = "Institution Domain"
        verbose_name_plural = "Institution Domains"

    def save(self, *args, **kwargs):
        self.domain = self.domain.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.domain


class InstitutionContact(BaseModel):

    class ContactType(models.TextChoices):
        ADMINISTRATIVE = "ADMINISTRATIVE", "Administrative"
        TECHNICAL = "TECHNICAL", "Technical"
        COMPLIANCE = "COMPLIANCE", "Compliance"
        FINANCE = "FINANCE", "Finance"
        SUPPORT = "SUPPORT", "Support"

    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="contacts"
    )

    name = models.CharField(
        max_length=255
    )

    email = models.EmailField()

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    designation = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    contact_type = models.CharField(
        max_length=30,
        choices=ContactType.choices,
        default=ContactType.ADMINISTRATIVE
    )

    is_primary = models.BooleanField(
        default=False
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Institution Contact"
        verbose_name_plural = "Institution Contacts"
        constraints = [
            models.UniqueConstraint(
                fields=["institution"],
                condition=models.Q(is_primary=True),
                name="unique_primary_contact_per_institution",
            )
        ]
        indexes = [
            models.Index(fields=["institution", "contact_type"]),
            models.Index(fields=["institution", "is_primary"]),
        ]

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()

        if self.name:
            self.name = self.name.strip()

        if self.designation:
            self.designation = self.designation.strip()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.institution.name})"


class InstitutionInvite(BaseModel):

    class InviteStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        EXPIRED = "EXPIRED", "Expired"
        CANCELLED = "CANCELLED", "Cancelled"

    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="invites"
    )

    email = models.EmailField()

    token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    invited_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="institution_invites_sent"
    )

    status = models.CharField(
        max_length=20,
        choices=InviteStatus.choices,
        default=InviteStatus.PENDING,
        db_index=True
    )

    expires_at = models.DateTimeField()

    accepted_at = models.DateTimeField(
        blank=True,
        null=True
    )

    is_used = models.BooleanField(
        default=False
    )

    message = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Institution Invite"
        verbose_name_plural = "Institution Invites"
        indexes = [
            models.Index(fields=["institution", "status"]),
            models.Index(fields=["email", "status"]),
            models.Index(fields=["expires_at"]),
        ]

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class InstitutionRequest(BaseModel):

    class RequestStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        REVIEWING = "REVIEWING", "Reviewing"
        CONTACTED = "CONTACTED", "Contacted"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        ARCHIVED = "ARCHIVED", "Archived"

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="institution_requests"
    )

    institution_name = models.CharField(
        max_length=255
    )

    website = models.URLField(
        blank=True,
        null=True
    )

    domain = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    country = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    requested_email = models.EmailField(
        blank=True,
        null=True
    )

    notes = models.TextField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING,
        db_index=True
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_institution_requests"
    )

    reviewed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    contacted_at = models.DateTimeField(
        blank=True,
        null=True
    )

    converted_institution = models.ForeignKey(
        Institution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_requests"
    )

    admin_notes = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Institution Request"
        verbose_name_plural = "Institution Requests"
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["institution_name"]),
            models.Index(fields=["domain"]),
        ]

    def save(self, *args, **kwargs):
        if self.institution_name:
            self.institution_name = self.institution_name.strip()

        if self.website:
            self.website = self.website.strip()

        if self.domain:
            self.domain = self.domain.strip().lower()

        if self.requested_email:
            self.requested_email = self.requested_email.strip().lower()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.institution_name

class InstitutionStaff(BaseModel):

    class StaffRole(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        REVIEWER = "REVIEWER", "Reviewer"
        OPERATOR = "OPERATOR", "Operator"

    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="staff_members"
    )

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="institution_staff_roles"
    )

    role = models.CharField(
        max_length=30,
        choices=StaffRole.choices,
        default=StaffRole.REVIEWER
    )

    is_primary_contact = models.BooleanField(
        default=False
    )

    is_active = models.BooleanField(
        default=True
    )

    joined_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = (
            "institution",
            "user",
        )

        ordering = ["-created_at"]

        verbose_name = "Institution Staff"
        verbose_name_plural = "Institution Staff"

    def __str__(self):
        return f"{self.user.email} - {self.institution.name}"


class InstitutionDocument(BaseModel):

    class DocumentType(models.TextChoices):
        LICENSE = "LICENSE", "License"
        ACCREDITATION = "ACCREDITATION", "Accreditation"
        GOVERNMENT_ID = "GOVERNMENT_ID", "Government ID"
        TAX_DOCUMENT = "TAX_DOCUMENT", "Tax Document"
        OTHER = "OTHER", "Other"

    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="documents"
    )

    uploaded_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="institution_documents_uploaded"
    )

    document_type = models.CharField(
        max_length=30,
        choices=DocumentType.choices
    )

    title = models.CharField(
        max_length=255
    )

    file = models.FileField(
        upload_to="institutions/documents/"
    )

    notes = models.TextField(
        blank=True,
        null=True
    )

    is_verified = models.BooleanField(
        default=False
    )

    verified_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_institution_documents"
    )

    verified_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["-created_at"]

        verbose_name = "Institution Document"
        verbose_name_plural = "Institution Documents"

    def __str__(self):
        return self.title