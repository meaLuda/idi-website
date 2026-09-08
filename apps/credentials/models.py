"""Certificate records for the DIDA credential-verification service.

Deliberately in its own app rather than ``apps.home``:

* ``apps.home``'s migration history contains vendor-branched raw SQL (0002, 0003)
  and a table created without Django model state, retro-fitted later by 0005. The
  SQLite and PostgreSQL schemas there were produced by different code paths. This
  app's migrations are generated purely from model state and apply identically on
  both -- the property you want for the table that decides whether a certificate
  is genuine.
* It yields a clean permission set, so a "Registrar" group can issue certificates
  without gaining any access to the marketing site.

There is deliberately **no ForeignKey to home.Program**. Every field a certificate
displays is snapshotted onto the certificate itself, so the FK would buy almost
nothing while coupling this app to that migration graph. ``program_slug`` records
the association as a plain string.
"""

from __future__ import annotations

import hashlib

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone

from .storage import certificate_pdf_path, certificate_storage
from .tokens import TOKEN_LENGTH, format_code, generate_code
from .validators import PdfMagicBytesValidator, validate_pdf_size

# Fields that must never change once a certificate leaves draft. This is the set
# the immutability guard freezes and the admin renders read-only.
FROZEN_FIELDS = (
    'serial',
    'token',
    'recipient_full_name',
    'program_title',
    'program_type_label',
    'credential_title',
    'duration_text',
    'format',
    'signatory_1_name',
    'signatory_1_title',
    'signatory_2_name',
    'signatory_2_title',
    'completion_date',
    'issue_date',
)

# Snapshot fields copied from the cohort on first save, and never re-synced.
SNAPSHOT_FROM_COHORT = (
    'program_slug',
    'program_title',
    'program_type_label',
    'credential_title',
    'duration_text',
    'format',
    'signatory_1_name',
    'signatory_1_title',
    'signatory_2_name',
    'signatory_2_title',
)


class SerialSequence(models.Model):
    """Allocator for human-readable certificate serials.

    Computing ``MAX(n) + 1`` would race across the four gunicorn workers and could
    issue duplicate serials on documents that carry legal weight. Allocation takes
    a row lock instead (a no-op on SQLite, which is single-writer anyway).
    """

    prefix = models.CharField(max_length=24, default='DIDA-IDI')
    year = models.PositiveSmallIntegerField()
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Serial sequence'
        verbose_name_plural = 'Serial sequences'
        constraints = [
            models.UniqueConstraint(fields=['prefix', 'year'], name='uniq_serial_prefix_year'),
        ]

    def __str__(self):
        return f'{self.prefix}-{self.year} (last {self.last_number:05d})'

    @classmethod
    def allocate(cls, year, prefix='DIDA-IDI'):
        """Return the next serial string, e.g. ``DIDA-IDI-2026-00567``."""
        with transaction.atomic():
            row, _ = cls.objects.select_for_update().get_or_create(
                prefix=prefix, year=year,
            )
            row.last_number += 1
            row.save(update_fields=['last_number'])
            return f'{prefix}-{year}-{row.last_number:05d}'


class Cohort(models.Model):
    """A group of recipients sharing a programme and dates.

    Exists to make one-at-a-time issuance fast: selecting a cohort pre-fills the
    snapshot fields, so a registrar types a name and two dates rather than twelve
    fields per certificate.
    """

    name = models.CharField(max_length=120, help_text="e.g. 'DIDA Executive Cohort 3'")
    code = models.CharField(max_length=24, unique=True, help_text="e.g. 'EXEC-2026-C3'")

    program_slug = models.CharField(
        max_length=60, blank=True,
        help_text='Slug of the related home.Program, if any. Plain text by design.',
    )
    program_title = models.CharField(max_length=200)
    program_type_label = models.CharField(max_length=60, blank=True, help_text="e.g. 'Executive Program'")
    credential_title = models.CharField(max_length=200, default='Certificate of Completion')

    year = models.PositiveSmallIntegerField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    default_completion_date = models.DateField(null=True, blank=True)
    default_issue_date = models.DateField(null=True, blank=True)

    duration_text = models.CharField(max_length=100, blank=True, help_text="e.g. '12 weeks'")
    format = models.CharField(max_length=100, blank=True, help_text="e.g. 'Hybrid - Nairobi'")
    venue = models.CharField(max_length=200, blank=True)

    signatory_1_name = models.CharField(max_length=120, blank=True)
    signatory_1_title = models.CharField(max_length=160, blank=True)
    signatory_2_name = models.CharField(max_length=120, blank=True)
    signatory_2_title = models.CharField(max_length=160, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year', 'name']
        verbose_name = 'Cohort'
        verbose_name_plural = 'Cohorts'

    def __str__(self):
        return f'{self.name} ({self.year})'


class Certificate(models.Model):
    """A single issued credential.

    Immutability is enforced in three layers, because any one alone is bypassable:
      1. Snapshot fields, filled from the cohort only when blank and never re-synced.
      2. ``save()`` raises if a frozen field changes on a non-draft record.
      3. The admin renders the frozen set read-only once the record leaves draft.

    Corrections go through revoke + reissue + ``superseded_by``, never by editing,
    so a certificate already in circulation keeps resolving and points at its
    replacement.
    """

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        ISSUED = 'issued', 'Issued'
        REVOKED = 'revoked', 'Revoked'
        SUPERSEDED = 'superseded', 'Superseded'

    # --- Identity ---------------------------------------------------------
    serial = models.CharField(
        max_length=32, unique=True, db_index=True,
        help_text='Human-readable record number printed on the certificate.',
    )
    token = models.CharField(
        max_length=TOKEN_LENGTH, unique=True, db_index=True,
        help_text='Unguessable verification code. Canonical form: uppercase, no hyphens.',
    )

    # --- Recipient --------------------------------------------------------
    recipient_full_name = models.CharField(max_length=160, help_text='Exactly as printed.')
    recipient_email = models.EmailField(blank=True, help_text='Internal only. Never shown publicly.')
    recipient_country = models.CharField(max_length=2, blank=True, help_text='ISO 3166-1 alpha-2.')

    # --- Credential (snapshots; authoritative once issued) ----------------
    cohort = models.ForeignKey(
        Cohort, null=True, blank=True, on_delete=models.SET_NULL, related_name='certificates',
    )
    program_slug = models.CharField(max_length=60, blank=True)
    program_title = models.CharField(max_length=200)
    program_type_label = models.CharField(max_length=60, blank=True)
    credential_title = models.CharField(max_length=200, default='Certificate of Completion')
    duration_text = models.CharField(max_length=100, blank=True)
    format = models.CharField(max_length=100, blank=True)
    venue = models.CharField(max_length=200, blank=True)

    signatory_1_name = models.CharField(max_length=120, blank=True)
    signatory_1_title = models.CharField(max_length=160, blank=True)
    signatory_2_name = models.CharField(max_length=120, blank=True)
    signatory_2_title = models.CharField(max_length=160, blank=True)

    # --- Dates ------------------------------------------------------------
    # DateField, not DateTimeField: a calendar date has no time zone, and storing
    # one would render a day off for readers outside the server's zone.
    completion_date = models.DateField()
    issue_date = models.DateField()
    expires_on = models.DateField(null=True, blank=True, help_text='Blank = never expires.')

    # --- Status -----------------------------------------------------------
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True)
    superseded_by = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='supersedes',
    )
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
    )
    revocation_reason = models.TextField(blank=True, help_text='Internal. Never shown publicly.')
    revocation_public_note = models.CharField(
        max_length=200, blank=True, help_text='Shown on the public verification page.',
    )

    # --- Archived document -------------------------------------------------
    # Stored on a private, non-website bucket and never linked publicly. See
    # storage.py for why a plain media FileField would publish these worldwide.
    pdf = models.FileField(
        upload_to=certificate_pdf_path,
        storage=certificate_storage,
        blank=True, null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf']),
            PdfMagicBytesValidator(),
            validate_pdf_size,
        ],
        help_text='Archival copy. Admin only — never shown on the public page.',
    )
    pdf_sha256 = models.CharField(
        max_length=64, blank=True, db_index=True,
        help_text=(
            'Fingerprint of the stored PDF. Lets staff compare a file someone '
            'emailed them against the archived original.'
        ),
    )
    pdf_size = models.PositiveIntegerField(null=True, blank=True)

    # --- Provenance -------------------------------------------------------
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
    )
    issued_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text='Internal. Never shown publicly.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- Scan counters (denormalised; updated via F() on the scan path) ---
    scan_count = models.PositiveIntegerField(default=0)
    first_scanned_at = models.DateTimeField(null=True, blank=True)
    last_scanned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-issue_date', '-id']
        verbose_name = 'Certificate'
        verbose_name_plural = 'Certificates'
        indexes = [
            models.Index(fields=['status', 'issue_date'], name='cert_status_issued_idx'),
            models.Index(fields=['cohort', 'status'], name='cert_cohort_status_idx'),
            models.Index(fields=['recipient_full_name'], name='cert_recipient_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    ~models.Q(status='revoked') | models.Q(revoked_at__isnull=False)
                ),
                name='cert_revoked_requires_timestamp',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(expires_on__isnull=True)
                    | models.Q(expires_on__gte=models.F('issue_date'))
                ),
                name='cert_expiry_after_issue',
            ),
        ]

    def __str__(self):
        return f'{self.serial} - {self.recipient_full_name}'

    # -- Immutability layer 2 ---------------------------------------------
    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        # Stash what the database actually held, so save() can detect edits to
        # fields that must not change after issuance.
        instance._loaded_values = dict(zip(field_names, values))
        return instance

    def _assert_frozen_fields_unchanged(self):
        loaded = getattr(self, '_loaded_values', None)
        if not loaded:
            return
        if loaded.get('status') == self.Status.DRAFT:
            return  # drafts are still editable
        changed = [
            name for name in FROZEN_FIELDS
            if name in loaded and loaded[name] != getattr(self, name)
        ]
        if changed:
            raise ValidationError(
                'A certificate that has left draft cannot be edited '
                f'({", ".join(changed)}). Revoke it and issue a replacement instead.'
            )

    def _apply_cohort_snapshots(self):
        """Copy cohort defaults into blank snapshot fields. Never re-syncs."""
        if not self.cohort_id:
            return
        for field in SNAPSHOT_FROM_COHORT:
            if not getattr(self, field, ''):
                setattr(self, field, getattr(self.cohort, field, '') or '')
        if not self.venue:
            self.venue = self.cohort.venue or ''
        if not self.completion_date and self.cohort.default_completion_date:
            self.completion_date = self.cohort.default_completion_date
        if not self.issue_date and self.cohort.default_issue_date:
            self.issue_date = self.cohort.default_issue_date

    def save(self, *args, **kwargs):
        self._assert_frozen_fields_unchanged()
        self._apply_cohort_snapshots()

        if not self.token:
            # Generate-and-insert, catching collisions, rather than checking for
            # existence first -- a check-then-insert races across workers.
            self.token = generate_code()
        if not self.serial:
            year = self.issue_date.year if self.issue_date else timezone.localdate().year
            self.serial = SerialSequence.allocate(year)
        self._refresh_pdf_fingerprint()
        super().save(*args, **kwargs)

    def _refresh_pdf_fingerprint(self):
        """Hash the PDF when a not-yet-committed file is attached.

        ``_committed`` is False only for a freshly assigned file, so re-saving an
        unchanged record does not re-download and re-hash the stored object. Same
        approach as downscale_image_field() in apps/home/models.py.
        """
        if not self.pdf:
            self.pdf_sha256 = ''
            self.pdf_size = None
            return
        if getattr(self.pdf, '_committed', True):
            return
        digest = hashlib.sha256()
        self.pdf.open()
        for chunk in self.pdf.chunks():
            digest.update(chunk)
        self.pdf.seek(0)
        self.pdf_sha256 = digest.hexdigest()
        self.pdf_size = self.pdf.size

    # -- Presentation ------------------------------------------------------
    @property
    def token_display(self):
        """Hyphenated form for printing and display."""
        return format_code(self.token)

    def get_absolute_url(self):
        return reverse('credentials:detail', kwargs={'code': self.token})

    def get_short_url(self):
        """The path encoded in the QR code."""
        return reverse('credentials:detail_short', kwargs={'code': self.token})

    # -- State -------------------------------------------------------------
    @property
    def is_expired(self):
        return bool(self.expires_on and self.expires_on < timezone.localdate())

    @property
    def public_state(self):
        """The state the public verification page renders.

        Draft is reported as 'not_found' so staff can prepare records without them
        being publicly resolvable, and so a draft is indistinguishable from a code
        that was never issued.
        """
        if self.status == self.Status.DRAFT:
            return 'not_found'
        if self.status == self.Status.REVOKED:
            return 'revoked'
        if self.status == self.Status.SUPERSEDED:
            return 'superseded'
        if self.is_expired:
            return 'expired'
        return 'valid'

    @property
    def is_publicly_valid(self):
        return self.public_state == 'valid'


class CertificateAuditEvent(models.Model):
    """Append-only record of what happened to a certificate.

    Django's admin LogEntry covers admin edits only -- not shell sessions or
    management commands -- and is not something you would show an auditor.
    """

    class Action(models.TextChoices):
        CREATED = 'created', 'Created'
        ISSUED = 'issued', 'Issued'
        REVOKED = 'revoked', 'Revoked'
        SUPERSEDED = 'superseded', 'Superseded'
        EDITED = 'edited', 'Edited'
        PDF_REPLACED = 'pdf_replaced', 'PDF replaced'

    certificate = models.ForeignKey(
        Certificate, on_delete=models.CASCADE, related_name='audit_events',
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
    )
    action = models.CharField(max_length=24, choices=Action.choices)
    changes = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at', '-id']
        verbose_name = 'Audit event'
        verbose_name_plural = 'Audit events'

    def __str__(self):
        return f'{self.certificate_id} {self.action} @ {self.created_at:%Y-%m-%d %H:%M}'


class CertificateScan(models.Model):
    """One verification lookup, de-duplicated to one row per person per day.

    Misses (``certificate=None``) live in the same table as hits: both analytics
    questions -- "how often was this cohort verified?" and "are we being
    enumerated?" -- are answered from here, and a second table would double the
    write path on the request that matters most.

    ``on_delete=SET_NULL`` plus the serial snapshot means deleting a certificate
    cannot silently erase the evidence that it was verified.
    """

    class Outcome(models.TextChoices):
        VALID = 'valid', 'Valid'
        REVOKED = 'revoked', 'Revoked'
        EXPIRED = 'expired', 'Expired'
        SUPERSEDED = 'superseded', 'Superseded'
        NOT_FOUND = 'not_found', 'Not found'
        MALFORMED = 'malformed', 'Malformed code'

    class Method(models.TextChoices):
        QR = 'qr', 'QR / short link'
        MANUAL = 'manual', 'Manual entry'
        DIRECT = 'direct', 'Direct link'

    certificate = models.ForeignKey(
        Certificate, null=True, blank=True, on_delete=models.SET_NULL, related_name='scans',
    )
    certificate_serial = models.CharField(max_length=32, blank=True)

    scanned_at = models.DateTimeField(default=timezone.now, db_index=True)
    outcome = models.CharField(max_length=12, choices=Outcome.choices, db_index=True)
    lookup_method = models.CharField(max_length=8, choices=Method.choices, default=Method.DIRECT)

    # Never a raw IP -- see scans.hash_ip() for why the salt is the whole control.
    ip_hash = models.CharField(max_length=64, blank=True, db_index=True)
    ua_hash = models.CharField(max_length=64, blank=True)
    ua_family = models.CharField(max_length=40, blank=True)
    is_bot = models.BooleanField(default=False, db_index=True)
    referer_host = models.CharField(max_length=120, blank=True, help_text='Host only; never a full URL.')

    dedupe_key = models.CharField(max_length=64, unique=True)
    hit_count = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scanned_at', '-id']
        verbose_name = 'Certificate scan'
        verbose_name_plural = 'Certificate scans'
        indexes = [
            models.Index(fields=['certificate', 'scanned_at'], name='scan_cert_time_idx'),
            models.Index(fields=['outcome', 'scanned_at'], name='scan_outcome_time_idx'),
        ]

    def __str__(self):
        return f'{self.outcome} @ {self.scanned_at:%Y-%m-%d %H:%M}'

    @staticmethod
    def build_dedupe_key(certificate_id, ip_hash, ua_hash, day):
        raw = f'{certificate_id or "none"}|{ip_hash}|{ua_hash}|{day.isoformat()}'
        return hashlib.sha256(raw.encode()).hexdigest()
