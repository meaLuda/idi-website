"""Issuing a certificate should not mean retyping the cohort's details.

Reported from production: selecting a cohort on the add form left every
programme field blank, and the form demanded a serial number even though
SerialSequence generates one on save.
"""

import datetime
import json

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.test import TestCase
from django.urls import reverse

from apps.credentials.admin import CertificateAdminForm
from apps.credentials.models import Certificate
from apps.credentials.tests.test_models import make_cohort
from apps.credentials.tests.utils import isolated_cache

User = get_user_model()


@isolated_cache
class SerialTests(TestCase):
    def test_serial_is_not_required_on_the_form(self):
        self.assertFalse(CertificateAdminForm().fields['serial'].required)

    def test_saving_without_a_serial_generates_one(self):
        cohort = make_cohort()
        form = CertificateAdminForm(data={
            'recipient_full_name': 'Ada Kimani',
            'cohort': cohort.pk,
            'status': Certificate.Status.ISSUED,
            'credential_title': 'Certificate of Completion',
            'completion_date': '2026-04-24',
            'issue_date': '2026-09-08',
        })
        self.assertTrue(form.is_valid(), form.errors)
        cert = form.save()
        self.assertRegex(cert.serial, r'^DIDA-IDI-2026-\d{5}$')

    def test_consecutive_certificates_get_consecutive_serials(self):
        cohort = make_cohort()
        serials = []
        for name in ('Ada Kimani', 'Brian Otieno', 'Cynthia Wanjiru'):
            serials.append(Certificate.objects.create(
                cohort=cohort, recipient_full_name=name,
                status=Certificate.Status.ISSUED,
                completion_date=datetime.date(2026, 4, 24),
                issue_date=datetime.date(2026, 9, 8),
            ).serial)
        self.assertEqual(len(set(serials)), 3)
        numbers = [int(s.rsplit('-', 1)[1]) for s in serials]
        self.assertEqual(numbers, sorted(numbers))


@isolated_cache
class CohortAutofillTests(TestCase):
    def setUp(self):
        self.cohort = make_cohort()
        self.user = User.objects.create_superuser('root', 'r@example.com', 'pw')
        self.client.force_login(self.user)

    def test_the_endpoint_returns_the_cohort_defaults(self):
        url = reverse('admin:credentials_cohort_defaults')
        response = self.client.get(url, {'cohort': self.cohort.pk})
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['program_title'], 'Decision Intelligence Foundations')
        self.assertEqual(data['program_type_label'], 'Executive Program')
        self.assertEqual(data['duration_text'], '12 weeks')
        self.assertEqual(data['signatory_1_name'], 'Pauline Kanana')
        self.assertEqual(data['venue'], 'The Moran AI and Cybersecurity, Center of Excellence')

    def test_dates_come_back_iso_formatted_for_the_date_widgets(self):
        self.cohort.default_completion_date = datetime.date(2026, 4, 24)
        self.cohort.default_issue_date = datetime.date(2026, 9, 8)
        self.cohort.save()
        response = self.client.get(
            reverse('admin:credentials_cohort_defaults'), {'cohort': self.cohort.pk},
        )
        data = json.loads(response.content)
        self.assertEqual(data['completion_date'], '2026-04-24')
        self.assertEqual(data['issue_date'], '2026-09-08')

    def test_unknown_cohort_returns_404_not_an_error_page(self):
        response = self.client.get(
            reverse('admin:credentials_cohort_defaults'), {'cohort': 999999},
        )
        self.assertEqual(response.status_code, 404)

    def test_anonymous_users_cannot_read_cohort_defaults(self):
        self.client.logout()
        response = self.client.get(
            reverse('admin:credentials_cohort_defaults'), {'cohort': self.cohort.pk},
        )
        self.assertIn(response.status_code, (302, 403))

    def test_the_add_page_loads_the_autofill_script_and_endpoint(self):
        html = self.client.get(reverse('admin:credentials_certificate_add')).content.decode()
        # ManifestStaticFilesStorage hashes the filename, so match the stem.
        self.assertRegex(html, r'credentials_cohort_autofill(\.[0-9a-f]+)?\.js')
        self.assertIn('data-cohort-defaults-url', html)


@isolated_cache
class MinimalEntryTests(TestCase):
    """The actual workflow: pick a cohort, type a name, save."""

    def setUp(self):
        self.cohort = make_cohort(
            default_completion_date=datetime.date(2026, 4, 24),
            default_issue_date=datetime.date(2026, 9, 8),
        )
        self.user = User.objects.create_superuser('root', 'r@example.com', 'pw')
        self.client.force_login(self.user)

    def test_a_cohort_and_a_name_are_enough(self):
        form = CertificateAdminForm(data={
            'recipient_full_name': 'Ada Kimani',
            'cohort': self.cohort.pk,
            'status': Certificate.Status.ISSUED,
        })
        self.assertTrue(form.is_valid(), form.errors)
        cert = form.save()

        # Everything below was typed by nobody.
        self.assertTrue(cert.serial)
        self.assertEqual(cert.program_title, 'Decision Intelligence Foundations')
        self.assertEqual(cert.credential_title, 'Certificate of Completion')
        self.assertEqual(cert.completion_date, datetime.date(2026, 4, 24))
        self.assertEqual(cert.issue_date, datetime.date(2026, 9, 8))
        self.assertEqual(cert.signatory_1_name, 'Pauline Kanana')

    def test_without_a_cohort_the_details_are_still_demanded(self):
        """Relaxing the form must not let a blank certificate through."""
        form = CertificateAdminForm(data={
            'recipient_full_name': 'Ada Kimani',
            'status': Certificate.Status.ISSUED,
        })
        self.assertFalse(form.is_valid())
        for field in ('program_title', 'completion_date', 'issue_date'):
            self.assertIn(field, form.errors)

    def test_typed_values_beat_cohort_defaults(self):
        form = CertificateAdminForm(data={
            'recipient_full_name': 'Ada Kimani',
            'cohort': self.cohort.pk,
            'status': Certificate.Status.ISSUED,
            'program_title': 'Bespoke Programme',
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().program_title, 'Bespoke Programme')


@isolated_cache
class CorrectabilityTests(TestCase):
    """Certificates must stay correctable until someone has actually verified one.

    Reported from production: 26 certificates were issued and every field on all
    of them was read-only, so a mistyped recipient name could not be fixed.
    """

    def setUp(self):
        self.cohort = make_cohort()
        self.cert = Certificate.objects.create(
            cohort=self.cohort, recipient_full_name='Ada Kimani',
            status=Certificate.Status.ISSUED,
            completion_date=datetime.date(2026, 4, 24),
            issue_date=datetime.date(2026, 9, 8),
        )

    def test_a_freshly_issued_certificate_is_not_locked(self):
        self.assertEqual(self.cert.scan_count, 0)
        self.assertFalse(self.cert.is_locked)

    def test_a_typo_can_be_corrected_before_anyone_verifies(self):
        cert = Certificate.objects.get(pk=self.cert.pk)
        cert.recipient_full_name = 'Ada Nyambura Kimani'
        cert.save()
        cert.refresh_from_db()
        self.assertEqual(cert.recipient_full_name, 'Ada Nyambura Kimani')

    def test_it_locks_after_the_first_verification(self):
        Certificate.objects.filter(pk=self.cert.pk).update(scan_count=1)
        cert = Certificate.objects.get(pk=self.cert.pk)
        self.assertTrue(cert.is_locked)
        cert.recipient_full_name = 'Changed After Verification'
        with self.assertRaises(ValidationError):
            cert.save()

    def test_revoked_certificates_are_locked_even_if_never_verified(self):
        Certificate.objects.filter(pk=self.cert.pk).update(
            status=Certificate.Status.REVOKED, revoked_at=timezone.now(),
        )
        self.assertTrue(Certificate.objects.get(pk=self.cert.pk).is_locked)

    def test_verifying_it_through_the_public_page_locks_it(self):
        """End to end: a real lookup is what flips the lock."""
        self.client.get(
            f'/verify/{self.cert.token}/',
            HTTP_USER_AGENT='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)',
            REMOTE_ADDR='41.90.1.1',
        )
        self.cert.refresh_from_db()
        self.assertEqual(self.cert.scan_count, 1)
        self.assertTrue(self.cert.is_locked)

    def test_the_admin_reports_why_a_record_is_locked(self):
        from django.contrib.admin.sites import site
        admin = site._registry[Certificate]
        self.assertIn('Editable', admin.lock_state(self.cert))

        Certificate.objects.filter(pk=self.cert.pk).update(scan_count=2)
        self.cert.refresh_from_db()
        state = admin.lock_state(self.cert)
        self.assertIn('Locked', state)
        self.assertIn('verified 2 time(s)', state)
