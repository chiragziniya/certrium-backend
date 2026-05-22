import uuid

from django.conf import settings
from django.db import models

from common.models import BaseModel


class PaymentTransaction(BaseModel):

    class PaymentType(models.TextChoices):
        WALLET_ACTIVATION = "WALLET_ACTIVATION", "Wallet Activation"
        VERIFICATION = "VERIFICATION", "Verification"
        EMPLOYER_ACCESS = "EMPLOYER_ACCESS", "Employer Access"
        INSTITUTION_BILLING = "INSTITUTION_BILLING", "Institution Billing"
        SUBSCRIPTION = "SUBSCRIPTION", "Subscription"

    class PaymentStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"
        CANCELLED = "CANCELLED", "Cancelled"

    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_transactions"
    )

    payment_type = models.CharField(
        max_length=30,
        choices=PaymentType.choices
    )

    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    currency = models.CharField(
        max_length=10,
        default="USD"
    )

    stripe_payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True
    )

    stripe_checkout_session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True
    )

    stripe_customer_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    metadata = models.JSONField(
        default=dict,
        blank=True
    )

    paid_at = models.DateTimeField(
        blank=True,
        null=True
    )

    failed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    refunded_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Payment Transaction"
        verbose_name_plural = "Payment Transactions"
        indexes = [
            models.Index(fields=["payment_type", "status"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["paid_at"]),
        ]

    def __str__(self):
        return f"{self.transaction_id}"


class Invoice(BaseModel):

    class InvoiceStatus(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ISSUED = "ISSUED", "Issued"
        PAID = "PAID", "Paid"
        OVERDUE = "OVERDUE", "Overdue"
        CANCELLED = "CANCELLED", "Cancelled"

    invoice_number = models.CharField(
        max_length=100,
        unique=True
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices"
    )

    employer = models.ForeignKey(
        "employers.Employer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices"
    )

    institution = models.ForeignKey(
        "institutions.Institution",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices"
    )

    transaction = models.OneToOneField(
        PaymentTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoice"
    )

    status = models.CharField(
        max_length=20,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.DRAFT,
        db_index=True
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    currency = models.CharField(
        max_length=10,
        default="USD"
    )

    issued_at = models.DateTimeField(
        blank=True,
        null=True
    )

    due_date = models.DateField(
        blank=True,
        null=True
    )

    paid_at = models.DateTimeField(
        blank=True,
        null=True
    )

    pdf_file = models.FileField(
        upload_to="payments/invoices/",
        blank=True,
        null=True
    )

    notes = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
        indexes = [
            models.Index(fields=["status", "issued_at"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["employer", "status"]),
            models.Index(fields=["institution", "status"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self):
        return self.invoice_number


class SubscriptionPlan(BaseModel):

    class BillingInterval(models.TextChoices):
        MONTHLY = "MONTHLY", "Monthly"
        YEARLY = "YEARLY", "Yearly"

    name = models.CharField(
        max_length=255
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    stripe_price_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    currency = models.CharField(
        max_length=10,
        default="USD"
    )

    billing_interval = models.CharField(
        max_length=20,
        choices=BillingInterval.choices,
        default=BillingInterval.MONTHLY,
        db_index=True
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True
    )

    features = models.JSONField(
        default=list,
        blank=True
    )

    class Meta:
        ordering = ["amount"]
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"
        indexes = [
            models.Index(fields=["billing_interval", "is_active"]),
            models.Index(fields=["amount"]),
        ]

    def __str__(self):
        return self.name


class UserSubscription(BaseModel):

    class SubscriptionStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        CANCELLED = "CANCELLED", "Cancelled"
        EXPIRED = "EXPIRED", "Expired"
        PAST_DUE = "PAST_DUE", "Past Due"
        TRIALING = "TRIALING", "Trialing"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions"
    )

    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.CASCADE,
        related_name="subscriptions"
    )

    stripe_subscription_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True
    )

    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE
    )

    started_at = models.DateTimeField()

    expires_at = models.DateTimeField(
        blank=True,
        null=True
    )

    cancelled_at = models.DateTimeField(
        blank=True,
        null=True
    )

    auto_renew = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "User Subscription"
        verbose_name_plural = "User Subscriptions"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["plan", "status"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"