"""Model-level tests, concentrated on the properties that make a certificate
defensible: immutability after issuance, correct public state, and unique
identifiers under concurrency.
"""

import datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.credentials import tokens
from apps.credentials.models import Certificate, Cohort, SerialSequence


def make_cohort(**overrides):
    defaults = dict(
        name='DIDA Executive Cohort 3',
        code='EXEC-2026-C3',
        program_slug='decision-intelligence-foundations',
        program_title='Decision Intelligence Foundations',
        program_type_label='Executive Program',
        year=2026,
        duration_text='12 weeks',
        format='Hybrid - Nairobi',
        venue='The Moran AI and Cybersecurity, Center of Excellence',
        signatory_1_name='Pauline Kanana',
        signatory_1_title='Co-Founder & Managing Partner',
        signatory_2_name='Munyala Mwalo',
        signatory_2_title='Co-Founder & Chief Decision Intelligence Director',
    )
    defaults.update(overrides)
    return Cohort.objects.create(**defaults)


def make_certificate(cohort=None, **overrides):
    defaults = dict(
        recipient_full_name='Ada Kimani',
        completion_date=datetime.date(2026, 4, 24),
        issue_date=datetime.date(2026, 9, 8),
        status=Certificate.Status.ISSUED,
        cohort=cohort,
    )
    defaults.update(overrides)
    if defaults.get('cohort') is None and 'program_title' not in defaults:
        defaults['program_title'] = 'Decision Intelligence Foundations'
    return Certificate.objects.create(**defaults)


class IdentifierTests(TestCase):
    def test_token_and_serial_are_generated_on_save(self):
        cert = make_certificate(make_cohort())
        self.assertTrue(tokens.is_valid_code(cert.token))
        self.assertRegex(cert.serial, r'^DIDA-IDI-2026-\d{5}$')

    def test_token_display_is_hyphenated(self):
        cert = make_certificate(make_cohort())
        self.assertEqual(cert.token_display, tokens.format_code(cert.token))
        self.assertEqual(cert.token_display.count('-'), 2)

    def test_duplicate_token_is_rejected_by_the_database(self):
        """The uniqueness guarantee must be a real constraint, not just Python."""
        cohort = make_cohort()
        first = make_certificate(cohort)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Certificate.objects.create(
                    recipient_full_name='Someone Else',
                    program_title='X',
                    completion_date=datetime.date(2026, 1, 1),
                    issue_date=datetime.date(2026, 1, 2),
                    token=first.token,
                )

    def test_serial_sequence_produces_no_gaps_or_repeats(self):
        serials = [SerialSequence.allocate(2026) for _ in range(50)]
        self.assertEqual(len(set(serials)), 50)
        numbers = sorted(int(s.rsplit('-', 1)[1]) for s in serials)
        self.assertEqual(numbers, list(range(1, 51)))

    def test_serials_are_scoped_per_year(self):
        a = SerialSequence.allocate(2026)
        b = SerialSequence.allocate(2027)
        self.assertTrue(a.endswith('00001'))
        self.assertTrue(b.endswith('00001'))
        self.assertIn('2026', a)
        self.assertIn('2027', b)


class SnapshotTests(TestCase):
    def test_snapshots_are_copied_from_the_cohort(self):
        cohort = make_cohort()
        cert = make_certificate(cohort)
        self.assertEqual(cert.program_title, 'Decision Intelligence Foundations')
        self.assertEqual(cert.signatory_1_name, 'Pauline Kanana')
        self.assertEqual(cert.duration_text, '12 weeks')

    def test_renaming_the_programme_does_not_change_an_issued_certificate(self):
        """The central immutability property."""
        cohort = make_cohort()
        cert = make_certificate(cohort)

        cohort.program_title = 'Completely Different Programme Name'
        cohort.signatory_1_name = 'Someone Else'
        cohort.save()

        cert.refresh_from_db()
        self.assertEqual(cert.program_title, 'Decision Intelligence Foundations')
        self.assertEqual(cert.signatory_1_name, 'Pauline Kanana')

    def test_deleting_the_cohort_leaves_the_certificate_verifiable(self):
        cohort = make_cohort()
        cert = make_certificate(cohort)
        cohort.delete()

        cert.refresh_from_db()
        self.assertIsNone(cert.cohort)
        self.assertEqual(cert.program_title, 'Decision Intelligence Foundations')
        self.assertEqual(cert.public_state, 'valid')

    def test_explicit_values_are_not_overwritten_by_cohort_defaults(self):
        cohort = make_cohort()
        cert = make_certificate(cohort, program_title='Bespoke Title')
        self.assertEqual(cert.program_title, 'Bespoke Title')


class ImmutabilityTests(TestCase):
    def test_editing_an_issued_certificate_raises(self):
        cert = make_certificate(make_cohort())
        cert = Certificate.objects.get(pk=cert.pk)  # reload so _loaded_values is set
        cert.recipient_full_name = 'Someone Entirely Different'
        with self.assertRaises(ValidationError):
            cert.save()

    def test_editing_each_frozen_field_raises(self):
        cert = make_certificate(make_cohort())
        for field, value in [
            ('recipient_full_name', 'Other Person'),
            ('program_title', 'Other Programme'),
            ('completion_date', datetime.date(2020, 1, 1)),
            ('issue_date', datetime.date(2020, 1, 2)),
            ('credential_title', 'Other Credential'),
        ]:
            fresh = Certificate.objects.get(pk=cert.pk)
            setattr(fresh, field, value)
            with self.assertRaises(ValidationError, msg=f'{field} was editable'):
                fresh.save()

    def test_drafts_remain_editable(self):
        cert = make_certificate(make_cohort(), status=Certificate.Status.DRAFT)
        cert = Certificate.objects.get(pk=cert.pk)
        cert.recipient_full_name = 'Corrected Name'
        cert.save()
        cert.refresh_from_db()
        self.assertEqual(cert.recipient_full_name, 'Corrected Name')

    def test_status_and_revocation_stay_editable_after_issue(self):
        cert = make_certificate(make_cohort())
        cert = Certificate.objects.get(pk=cert.pk)
        cert.status = Certificate.Status.REVOKED
        cert.revoked_at = timezone.now()
        cert.revocation_public_note = 'Reissued as DIDA-IDI-2026-00612'
        cert.save()
        cert.refresh_from_db()
        self.assertEqual(cert.status, Certificate.Status.REVOKED)

    def test_scan_counter_update_bypasses_the_guard(self):
        """Counters use .update(), which must not trip immutability."""
        from django.db.models import F
        cert = make_certificate(make_cohort())
        Certificate.objects.filter(pk=cert.pk).update(scan_count=F('scan_count') + 1)
        cert.refresh_from_db()
        self.assertEqual(cert.scan_count, 1)


class PublicStateTests(TestCase):
    def setUp(self):
        self.cohort = make_cohort()

    def test_issued_is_valid(self):
        self.assertEqual(make_certificate(self.cohort).public_state, 'valid')

    def test_draft_reads_as_not_found(self):
        cert = make_certificate(self.cohort, status=Certificate.Status.DRAFT)
        self.assertEqual(cert.public_state, 'not_found')

    def test_revoked(self):
        cert = make_certificate(
            self.cohort, status=Certificate.Status.REVOKED, revoked_at=timezone.now(),
        )
        self.assertEqual(cert.public_state, 'revoked')

    def test_expired(self):
        # Expiry must still be on or after the issue date (enforced by
        # cert_expiry_after_issue), so back-date the issue too.
        cert = make_certificate(
            self.cohort,
            issue_date=datetime.date(2020, 1, 1),
            completion_date=datetime.date(2019, 12, 1),
            expires_on=timezone.localdate() - datetime.timedelta(days=1),
        )
        self.assertEqual(cert.public_state, 'expired')
        self.assertTrue(cert.is_expired)

    def test_future_expiry_is_still_valid(self):
        cert = make_certificate(
            self.cohort, expires_on=timezone.localdate() + datetime.timedelta(days=1),
        )
        self.assertEqual(cert.public_state, 'valid')

    def test_superseded(self):
        cert = make_certificate(self.cohort, status=Certificate.Status.SUPERSEDED)
        self.assertEqual(cert.public_state, 'superseded')


class ConstraintTests(TestCase):
    def test_expiry_before_issue_is_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Certificate.objects.create(
                    recipient_full_name='Ada Kimani',
                    program_title='X',
                    completion_date=datetime.date(2026, 1, 1),
                    issue_date=datetime.date(2026, 6, 1),
                    expires_on=datetime.date(2026, 1, 1),
                )

    def test_revoked_without_timestamp_is_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Certificate.objects.create(
                    recipient_full_name='Ada Kimani',
                    program_title='X',
                    completion_date=datetime.date(2026, 1, 1),
                    issue_date=datetime.date(2026, 6, 1),
                    status=Certificate.Status.REVOKED,
                )
