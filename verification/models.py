import uuid

from django.conf import settings
from django.db import models

from common.models import BaseModel
from institutions.models import Institution


class VerificationRecord(BaseModel):

    class VerificationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        MATCHED = "MATCHED", "Matched"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"
        EXPIRED = "EXPIRED", "Expired"
        REVOKED = "REVOKED", "Revoked"

    class CredentialType(models.TextChoices):
        DEGREE = "DEGREE", "Degree"
        DIPLOMA = "DIPLOMA", "Diploma"
        CERTIFICATE = "CERTIFICATE", "Certificate"
        TRANSCRIPT = "TRANSCRIPT", "Transcript"
        LICENSE = "LICENSE", "License"
        EMPLOYMENT = "EMPLOYMENT", "Employment"
        OTHER = "OTHER", "Other"

    verification_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verification_records"
    )

    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="verification_records"
    )

    credential_type = models.CharField(
        max_length=30,
        choices=CredentialType.choices
    )

    credential_name = models.CharField(
        max_length=255
    )

    credential_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True
    )

    issued_date = models.DateField(
        blank=True,
        null=True
    )

    expiry_date = models.DateField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=30,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    reviewed_at = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True
    )

    verified_at = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True
    )

    rejected_at = models.DateTimeField(
        blank=True,
        null=True
    )

    rejection_reason = models.TextField(
        blank=True,
        null=True
    )

    verification_notes = models.TextField(
        blank=True,
        null=True
    )

    metadata = models.JSONField(
        default=dict,
        blank=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verification_created_by"
    )

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verification_updated_by"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Verification Record"
        verbose_name_plural = "Verification Records"
        indexes = [
            models.Index(fields=["candidate", "status"]),
            models.Index(fields=["institution", "status"]),
            models.Index(fields=["status", "submitted_at"]),
        ]

    def __str__(self):
        return f"{self.candidate.email} - {self.credential_name}"


class CredentialDocument(BaseModel):

    class DocumentType(models.TextChoices):
        ORIGINAL = "ORIGINAL", "Original"
        TRANSCRIPT = "TRANSCRIPT", "Transcript"
        SUPPORTING = "SUPPORTING", "Supporting"
        IDENTITY = "IDENTITY", "Identity"

    verification_record = models.ForeignKey(
        VerificationRecord,
        on_delete=models.CASCADE,
        related_name="documents"
    )

    document_type = models.CharField(
        max_length=30,
        choices=DocumentType.choices,
        default=DocumentType.ORIGINAL
    )

    file = models.FileField(
        upload_to="verification/documents/"
    )

    file_name = models.CharField(
        max_length=255
    )

    file_size = models.PositiveBigIntegerField(
        blank=True,
        null=True
    )

    mime_type = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verification_documents_uploaded"
    )

    is_encrypted = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Credential Document"
        verbose_name_plural = "Credential Documents"
        indexes = [
            models.Index(fields=["verification_record", "document_type"]),
        ]

    def __str__(self):
        return self.file_name


class VerificationEvent(BaseModel):

    class EventType(models.TextChoices):
        CREATED = "CREATED", "Created"
        UPDATED = "UPDATED", "Updated"
        STATUS_CHANGED = "STATUS_CHANGED", "Status Changed"
        DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED", "Document Uploaded"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"
        REVOKED = "REVOKED", "Revoked"
        COMMENTED = "COMMENTED", "Commented"

    verification_record = models.ForeignKey(
        VerificationRecord,
        on_delete=models.CASCADE,
        related_name="events"
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verification_events"
    )

    event_type = models.CharField(
        max_length=30,
        choices=EventType.choices
    )

    previous_status = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    new_status = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    message = models.TextField(
        blank=True,
        null=True
    )

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True
    )

    user_agent = models.TextField(
        blank=True,
        null=True
    )

    metadata = models.JSONField(
        default=dict,
        blank=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Verification Event"
        verbose_name_plural = "Verification Events"
        indexes = [
            models.Index(fields=["verification_record", "created_at"]),
            models.Index(fields=["event_type", "created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.verification_record.verification_id}"


class VerificationRequest(BaseModel):

    class RequestStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        EXPIRED = "EXPIRED", "Expired"

    employer = models.ForeignKey(
        "employers.Employer",
        on_delete=models.CASCADE,
        related_name="verification_requests"
    )

    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verification_requests"
    )

    verification_record = models.ForeignKey(
        VerificationRecord,
        on_delete=models.CASCADE,
        related_name="verification_requests"
    )

    request_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING
    )

    requested_at = models.DateTimeField(
        auto_now_add=True
    )

    responded_at = models.DateTimeField(
        blank=True,
        null=True
    )

    expires_at = models.DateTimeField()

    employer_notes = models.TextField(
        blank=True,
        null=True
    )

    candidate_response_notes = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Verification Request"
        verbose_name_plural = "Verification Requests"
        constraints = [
            models.UniqueConstraint(
                fields=["employer", "candidate", "verification_record"],
                name="unique_verification_request_per_employer_candidate_record",
            )
        ]
        indexes = [
            models.Index(fields=["employer", "status"]),
            models.Index(fields=["candidate", "status"]),
            models.Index(fields=["verification_record", "status"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.employer.company_name} - {self.candidate.email}"

class VerificationComment(BaseModel):

    verification_record = models.ForeignKey(
        VerificationRecord,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verification_comments"
    )

    comment = models.TextField()

    is_internal = models.BooleanField(
        default=True,
        help_text="Internal comments visible only to staff/admins"
    )

    parent_comment = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies"
    )

    metadata = models.JSONField(
        default=dict,
        blank=True
    )

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Verification Comment"
        verbose_name_plural = "Verification Comments"

    def __str__(self):
        return f"Comment by {self.author}"