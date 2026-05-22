import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import UserManager


class User(AbstractUser):

    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        CANDIDATE = "CANDIDATE", "Candidate"
        INSTITUTION = "INSTITUTION", "Institution"
        EMPLOYER = "EMPLOYER", "Employer"
        REGULATOR = "REGULATOR", "Regulator"
        AUDITOR = "AUDITOR", "Auditor"
        OPERATIONS = "OPERATIONS", "Operations"

    objects = UserManager()

    # ==========================================
    # PRIMARY KEY
    # ==========================================
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # ==========================================
    # AUTH
    # ==========================================
    username = None

    email = models.EmailField(
        unique=True,
        db_index=True
    )

    role = models.CharField(
        max_length=30,
        choices=Roles.choices,
        default=Roles.CANDIDATE,
        db_index=True
    )

    # ==========================================
    # INSTITUTION RELATION
    # ==========================================
    institution = models.ForeignKey(
        "institutions.Institution",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users"
    )

    # ==========================================
    # PROFILE / SECURITY
    # ==========================================
    first_name = models.CharField(max_length=150)

    last_name = models.CharField(max_length=150)

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    is_email_verified = models.BooleanField(default=False)

    is_mfa_enabled = models.BooleanField(default=False)

    # ==========================================
    # AUDIT
    # ==========================================
    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["role", "institution"]),
            models.Index(fields=["is_email_verified", "is_mfa_enabled"]),
        ]

    # ==========================================
    # DJANGO AUTH SETTINGS
    # ==========================================
    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()

        if self.first_name:
            self.first_name = self.first_name.strip()

        if self.last_name:
            self.last_name = self.last_name.strip()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.email