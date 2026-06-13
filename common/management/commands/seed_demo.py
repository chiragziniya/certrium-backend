from __future__ import annotations

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from audit.models import ActivityTimeline, AuditLog, SecurityEvent
from common.models import MediaProvider, PlatformConfig
from common.media_storage import resolve_default_upload_provider
from employers.models import Employer, EmployerUser
from employers.models import EmployerVerificationAccess, EmployerVerificationReport
from institutions.models import (
    Institution,
    InstitutionContact,
    InstitutionDocument,
    InstitutionDomain,
    InstitutionInvite,
    InstitutionRequest,
    InstitutionStaff,
)
from payments.models import Invoice, PaymentTransaction, SubscriptionPlan
from payments.models import UserSubscription
from verification.models import CredentialDocument, VerificationEvent, VerificationRecord
from verification.models import VerificationComment, VerificationRequest
from wallets.models import Wallet, WalletRecord
from wallets.models import WalletAccessLog, WalletShare


_ONE_PIXEL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc\xf8\x0f\x00\x01\x01"
    b"\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


class Command(BaseCommand):
    help = "Seed a small set of demo data for local development (idempotent)."

    def handle(self, *args, **options):
        User = get_user_model()

        with transaction.atomic():
            # 1) Superuser
            admin_user, created = User.objects.update_or_create(
                email="admin@admin.com",
                defaults={
                    "is_staff": True,
                    "is_superuser": True,
                    "role": "ADMIN",
                    "first_name": "Admin",
                    "last_name": "User",
                },
            )
            admin_user.set_password("admin@123")
            admin_user.save(update_fields=["password", "is_staff", "is_superuser", "role", "first_name", "last_name"])  # noqa: E501

            self.stdout.write(
                self.style.SUCCESS(
                    f"Superuser ready: {admin_user.email} (password: admin@123){' [created]' if created else ''}"
                )
            )

            # 2) PlatformConfig singleton-ish
            config = PlatformConfig.objects.order_by("-updated_at").first()
            if not config:
                config = PlatformConfig.objects.create(
                    default_upload_provider=MediaProvider.LOCAL,
                    enable_local=True,
                    enable_cloudinary=True,
                    enable_s3=True,
                    smtp_host=None,
                    smtp_port=None,
                    smtp_username=None,
                    smtp_from_email=None,
                    smtp_use_tls=True,
                    smtp_use_ssl=False,
                    updated_by=admin_user,
                )
                self.stdout.write(self.style.SUCCESS("PlatformConfig created"))
            else:
                self.stdout.write(self.style.WARNING("PlatformConfig already exists; leaving as-is"))

            # 3) Institution
            institution, inst_created = Institution.objects.update_or_create(
                email="demo-institution@example.com",
                defaults={
                    "name": "Demo University",
                    "country": "US",
                    "city": "New York",
                    "status": Institution.Status.APPROVED,
                    "is_active": True,
                    "is_verified": True,
                    "onboarding_completed": True,
                },
            )

            if not institution.logo:
                institution.logo.save(
                    "demo-university.png",
                    ContentFile(_ONE_PIXEL_PNG),
                    save=True,
                )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Institution: {institution.email}{' [created]' if inst_created else ''}"
                )
            )

            InstitutionDomain.objects.get_or_create(
                domain="demo-university.edu",
                defaults={"institution": institution, "is_verified": True},
            )

            InstitutionContact.objects.get_or_create(
                institution=institution,
                email="registrar@demo-university.edu",
                defaults={
                    "name": "Registrar Office",
                    "phone_number": "+1-555-0101",
                    "designation": "Registrar",
                    "contact_type": InstitutionContact.ContactType.ADMINISTRATIVE,
                    "is_primary": True,
                },
            )

            # 4) Employer
            employer, emp_created = Employer.objects.update_or_create(
                email="demo-employer@example.com",
                defaults={
                    "company_name": "Demo Corp",
                    "country": "US",
                    "city": "San Francisco",
                    "status": Employer.Status.ACTIVE,
                    "is_active": True,
                    "is_verified": True,
                },
            )

            if not employer.logo:
                employer.logo.save(
                    "demo-corp.png",
                    ContentFile(_ONE_PIXEL_PNG),
                    save=True,
                )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Employer: {employer.email}{' [created]' if emp_created else ''}"
                )
            )

            # 5) Candidate user + wallet
            candidate, cand_created = User.objects.update_or_create(
                email="candidate@example.com",
                defaults={
                    "is_staff": False,
                    "is_superuser": False,
                    "role": "CANDIDATE",
                    "first_name": "Demo",
                    "last_name": "Candidate",
                    "is_email_verified": True,
                    "institution": institution,
                },
            )
            candidate.set_password("candidate@123")
            candidate.save()

            inst_staff_user, _ = User.objects.update_or_create(
                email="institution.staff@example.com",
                defaults={
                    "role": "INSTITUTION",
                    "first_name": "Inst",
                    "last_name": "Staff",
                    "is_email_verified": True,
                    "institution": institution,
                },
            )
            inst_staff_user.set_password("institution@123")
            inst_staff_user.save()

            employer_user, _ = User.objects.update_or_create(
                email="employer.user@example.com",
                defaults={
                    "role": "EMPLOYER",
                    "first_name": "Employer",
                    "last_name": "User",
                    "is_email_verified": True,
                },
            )
            employer_user.set_password("employer@123")
            employer_user.save()

            wallet, _ = Wallet.objects.get_or_create(owner=candidate)

            # 6) Employer membership
            EmployerUser.objects.get_or_create(
                employer=employer,
                user=admin_user,
                defaults={"role": EmployerUser.Role.ADMIN, "is_active": True},
            )

            EmployerUser.objects.get_or_create(
                employer=employer,
                user=employer_user,
                defaults={"role": EmployerUser.Role.RECRUITER, "is_active": True},
            )

            InstitutionStaff.objects.get_or_create(
                institution=institution,
                user=inst_staff_user,
                defaults={
                    "role": InstitutionStaff.StaffRole.REVIEWER,
                    "is_primary_contact": True,
                    "is_active": True,
                },
            )

            # 7) Verification record
            record = (
                VerificationRecord.objects.filter(candidate=candidate, institution=institution)
                .order_by("-created_at")
                .first()
            )
            if not record:
                record = VerificationRecord.objects.create(
                    candidate=candidate,
                    institution=institution,
                    credential_type=VerificationRecord.CredentialType.DEGREE,
                    credential_name="B.Sc. Computer Science",
                    credential_reference="DEMO-REF-001",
                    issued_date=date(2020, 6, 1),
                    status=VerificationRecord.VerificationStatus.PENDING,
                    created_by=admin_user,
                    updated_by=admin_user,
                )
                VerificationEvent.objects.create(
                    verification_record=record,
                    actor=admin_user,
                    event_type=VerificationEvent.EventType.CREATED,
                    message="Demo seed: created verification record",
                    metadata={"seeded": True},
                )
                self.stdout.write(self.style.SUCCESS("VerificationRecord created"))
            else:
                self.stdout.write(self.style.WARNING("VerificationRecord already exists; leaving as-is"))

            # Verification request + comment thread
            vreq, _ = VerificationRequest.objects.get_or_create(
                employer=employer,
                candidate=candidate,
                verification_record=record,
                defaults={
                    "status": VerificationRequest.RequestStatus.PENDING,
                    "expires_at": timezone.now() + timedelta(days=7),
                    "employer_notes": "Demo seed: please verify this credential.",
                },
            )

            root_comment, _ = VerificationComment.objects.get_or_create(
                verification_record=record,
                author=admin_user,
                comment="Demo seed: internal verification note.",
                defaults={"is_internal": True},
            )

            VerificationComment.objects.get_or_create(
                verification_record=record,
                author=inst_staff_user,
                parent_comment=root_comment,
                comment="Demo seed: reviewer response.",
                defaults={"is_internal": True},
            )

            # 8) Credential document (writes a small local file under MEDIA_ROOT)
            if not CredentialDocument.objects.filter(verification_record=record, file_name="demo-document.txt").exists():
                provider = resolve_default_upload_provider()
                doc = CredentialDocument(
                    verification_record=record,
                    document_type=CredentialDocument.DocumentType.ORIGINAL,
                    media_provider=provider,
                    file_name="demo-document.txt",
                    mime_type="text/plain",
                    uploaded_by=admin_user,
                    is_encrypted=False,
                )
                doc.file.save(
                    "demo-document.txt",
                    ContentFile(b"This is a demo document for provider-aware storage."),
                    save=False,
                )
                doc.file_size = doc.file.size
                doc.save()

                # Ensure we show persisted state.
                doc.refresh_from_db(fields=["media_provider", "file"])
                self.stdout.write(
                    self.style.SUCCESS(
                        f"CredentialDocument created (provider={doc.media_provider}, path={doc.file.name})"
                    )
                )
            else:
                self.stdout.write(self.style.WARNING("CredentialDocument already exists; leaving as-is"))

            # Institution document
            if not InstitutionDocument.objects.filter(institution=institution, title="Demo Accreditation").exists():
                provider = resolve_default_upload_provider()
                inst_doc = InstitutionDocument(
                    institution=institution,
                    uploaded_by=admin_user,
                    document_type=InstitutionDocument.DocumentType.ACCREDITATION,
                    title="Demo Accreditation",
                    media_provider=provider,
                    notes="Demo seed accreditation document",
                    is_verified=True,
                    verified_by=admin_user,
                    verified_at=timezone.now(),
                )
                inst_doc.file.save(
                    "demo-accreditation.pdf",
                    ContentFile(b"%PDF-1.4\n% Demo PDF\n"),
                    save=False,
                )
                inst_doc.save()

            # 9) Wallet record
            wallet_record, _ = WalletRecord.objects.get_or_create(wallet=wallet, verification_record=record)

            share, _ = WalletShare.objects.get_or_create(
                wallet_record=wallet_record,
                shared_by=candidate,
                shared_with_email="viewer@example.com",
                defaults={
                    "expires_at": timezone.now() + timedelta(days=14),
                    "status": WalletShare.ShareStatus.ACTIVE,
                },
            )

            WalletAccessLog.objects.get_or_create(
                wallet_share=share,
                accessed_by_email="viewer@example.com",
                defaults={
                    "ip_address": "127.0.0.1",
                    "user_agent": "seed-demo",
                },
            )

            # 10) Payment sample
            if not SubscriptionPlan.objects.exists():
                SubscriptionPlan.objects.create(
                    name="Starter",
                    description="Demo plan",
                    amount="9.99",
                    currency="USD",
                    billing_interval=SubscriptionPlan.BillingInterval.MONTHLY,
                    is_active=True,
                    features=["Demo feature"],
                )

            plan = SubscriptionPlan.objects.first()
            UserSubscription.objects.get_or_create(
                user=candidate,
                plan=plan,
                defaults={
                    "status": UserSubscription.SubscriptionStatus.ACTIVE,
                    "started_at": timezone.now() - timedelta(days=1),
                    "expires_at": timezone.now() + timedelta(days=29),
                    "auto_renew": True,
                },
            )

            tx = (
                PaymentTransaction.objects.filter(user=candidate)
                .order_by("-created_at")
                .first()
            )
            if not tx:
                tx = PaymentTransaction.objects.create(
                    user=candidate,
                    payment_type=PaymentTransaction.PaymentType.VERIFICATION,
                    amount="49.00",
                    currency="USD",
                    status=PaymentTransaction.PaymentStatus.SUCCESS,
                    paid_at=timezone.now(),
                    description="Demo seed payment",
                )

            Invoice.objects.get_or_create(
                invoice_number="INV-DEMO-0001",
                defaults={
                    "user": candidate,
                    "institution": institution,
                    "transaction": tx,
                    "status": Invoice.InvoiceStatus.PAID,
                    "subtotal": "49.00",
                    "tax_amount": "0.00",
                    "total_amount": "49.00",
                    "currency": "USD",
                    "issued_at": timezone.now(),
                    "paid_at": timezone.now(),
                    "media_provider": MediaProvider.AUTO,
                },
            )

            invoice = Invoice.objects.get(invoice_number="INV-DEMO-0001")
            if not invoice.pdf_file:
                invoice.pdf_file.save(
                    "invoice-demo.pdf",
                    ContentFile(b"%PDF-1.4\n% Demo invoice PDF\n"),
                    save=True,
                )

            # Employer access + report
            EmployerVerificationAccess.objects.get_or_create(
                employer=employer,
                candidate=candidate,
                verification_record=record,
                defaults={
                    "status": EmployerVerificationAccess.AccessStatus.APPROVED,
                    "requested_by": employer_user,
                    "approved_by_candidate": True,
                    "approved_at": timezone.now(),
                    "expires_at": timezone.now() + timedelta(days=30),
                    "employer_notes": "Demo seed: approved access",
                    "candidate_notes": "Demo seed: OK",
                },
            )

            if not EmployerVerificationReport.objects.filter(
                employer=employer,
                candidate=candidate,
                report_name="Demo Verification Report",
            ).exists():
                provider = resolve_default_upload_provider()
                report = EmployerVerificationReport(
                    employer=employer,
                    candidate=candidate,
                    generated_by=admin_user,
                    report_name="Demo Verification Report",
                    media_provider=provider,
                    expires_at=timezone.now() + timedelta(days=30),
                )
                report.report_file.save(
                    "demo-report.pdf",
                    ContentFile(b"%PDF-1.4\n% Demo report PDF\n"),
                    save=False,
                )
                report.save()

            # Institution invite + request
            InstitutionInvite.objects.get_or_create(
                institution=institution,
                email="new.staff@demo-university.edu",
                defaults={
                    "invited_by": admin_user,
                    "status": InstitutionInvite.InviteStatus.PENDING,
                    "expires_at": timezone.now() + timedelta(days=3),
                    "message": "Demo seed: welcome!",
                },
            )

            InstitutionRequest.objects.get_or_create(
                requested_by=candidate,
                institution_name="Requested Demo College",
                defaults={
                    "website": "https://requested.demo.edu",
                    "domain": "requested.demo.edu",
                    "country": "US",
                    "city": "Boston",
                    "requested_email": "contact@requested.demo.edu",
                    "notes": "Demo seed institution request",
                    "status": InstitutionRequest.RequestStatus.PENDING,
                    "reviewed_by": admin_user,
                },
            )

            # Audit + security + timeline
            AuditLog.objects.get_or_create(
                action_type=AuditLog.ActionType.VERIFICATION_CREATED,
                target_model="verification.VerificationRecord",
                target_id=str(record.pk),
                defaults={
                    "actor": admin_user,
                    "description": "Demo seed audit log",
                    "ip_address": "127.0.0.1",
                    "user_agent": "seed-demo",
                    "request_method": "POST",
                    "endpoint": "/api/verification/",
                    "metadata": {"seeded": True},
                },
            )

            SecurityEvent.objects.get_or_create(
                user=admin_user,
                event_type=SecurityEvent.EventType.LOGIN_SUCCESS,
                defaults={
                    "ip_address": "127.0.0.1",
                    "user_agent": "seed-demo",
                    "location": "Local",
                    "was_successful": True,
                    "details": {"seeded": True},
                },
            )

            ActivityTimeline.objects.get_or_create(
                user=candidate,
                title="Demo verification submitted",
                defaults={
                    "description": "Demo seed: candidate submitted a verification.",
                    "related_model": "verification.VerificationRecord",
                    "related_object_id": str(record.pk),
                    "icon": "verified",
                    "metadata": {"seeded": True},
                },
            )

        self.stdout.write(self.style.SUCCESS("Demo seed complete."))
