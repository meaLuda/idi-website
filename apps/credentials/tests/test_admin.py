"""Admin tests: permissions, immutability enforcement, and the artwork bridge."""

import csv
import io
import zipfile

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.credentials.models import Certificate, CertificateAuditEvent
from apps.credentials.tests.test_models import make_certificate, make_cohort
from apps.credentials.tests.utils import isolated_cache

User = get_user_model()


@isolated_cache
class AdminAccessTests(TestCase):
    def setUp(self):
        self.cohort = make_cohort()
        self.cert = make_certificate(self.cohort)
        self.superuser = User.objects.create_superuser('root', 'root@example.com', 'pw')

    def test_anonymous_cannot_download_a_qr(self):
        url = reverse('admin:credentials_certificate_qr_svg', args=[self.cert.pk])
        response = self.client.get(url)
        self.assertIn(response.status_code, (302, 403))
        self.assertNotEqual(response.status_code, 200)

    def test_staff_without_permission_is_denied(self):
        staff = User.objects.create_user('temp', 'temp@example.com', 'pw', is_staff=True)
        self.client.force_login(staff)
        url = reverse('admin:credentials_certificate_qr_svg', args=[self.cert.pk])
        self.assertIn(self.client.get(url).status_code, (302, 403))

    def test_superuser_gets_an_svg(self):
        self.client.force_login(self.superuser)
        url = reverse('admin:credentials_certificate_qr_svg', args=[self.cert.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/svg+xml')
        self.assertIn(self.cert.serial, response['Content-Disposition'])
        self.assertIn(b'<svg', response.content)

    def test_png_download(self):
        self.client.force_login(self.superuser)
        url = reverse('admin:credentials_certificate_qr_png', args=[self.cert.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'\x89PNG'))


@isolated_cache
class ReadonlyFieldTests(TestCase):
    def setUp(self):
        from apps.credentials.admin import CertificateAdmin
        from django.contrib.admin.sites import site
        self.admin = CertificateAdmin(Certificate, site)
        self.cohort = make_cohort()

    def _request(self):
        from django.test import RequestFactory
        request = RequestFactory().get('/admin/')
        request.user = User.objects.create_superuser('root', 'r@example.com', 'pw')
        return request

    def test_draft_fields_stay_editable(self):
        draft = make_certificate(self.cohort, status=Certificate.Status.DRAFT)
        readonly = self.admin.get_readonly_fields(self._request(), draft)
        self.assertNotIn('recipient_full_name', readonly)

    def test_verification_freezes_the_credential_fields(self):
        issued = make_certificate(self.cohort)
        Certificate.objects.filter(pk=issued.pk).update(scan_count=1)
        issued.refresh_from_db()
        readonly = self.admin.get_readonly_fields(self._request(), issued)
        for field in ('recipient_full_name', 'program_title', 'completion_date',
                      'issue_date', 'serial'):
            self.assertIn(field, readonly, f'{field} is still editable after issue')

    def test_an_unverified_issued_certificate_stays_editable(self):
        issued = make_certificate(self.cohort)
        readonly = self.admin.get_readonly_fields(self._request(), issued)
        self.assertNotIn('recipient_full_name', readonly)
        self.assertNotIn('program_title', readonly)

    def test_status_and_revocation_stay_editable(self):
        issued = make_certificate(self.cohort)
        readonly = self.admin.get_readonly_fields(self._request(), issued)
        self.assertNotIn('status', readonly)
        self.assertNotIn('revocation_public_note', readonly)


@isolated_cache
class ActionTests(TestCase):
    def setUp(self):
        self.cohort = make_cohort()
        self.superuser = User.objects.create_superuser('root', 'root@example.com', 'pw')
        self.client.force_login(self.superuser)
        self.changelist = reverse('admin:credentials_certificate_changelist')

    def test_merge_csv_contains_the_verify_url_and_no_email(self):
        cert = make_certificate(self.cohort, recipient_email='ada@example.com')
        response = self.client.post(self.changelist, {
            'action': 'export_merge_csv', '_selected_action': [cert.pk],
        })
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertNotIn('ada@example.com', body, 'recipient email leaked into the merge CSV')

        rows = list(csv.reader(io.StringIO(body)))
        header, row = rows[0], rows[1]
        self.assertIn('verify_url', header)
        self.assertIn('verification_code', header)
        self.assertIn(cert.serial, row)
        self.assertIn(cert.token_display, row)

    def test_qr_pack_is_a_zip_of_svgs(self):
        certs = [make_certificate(self.cohort) for _ in range(3)]
        response = self.client.post(self.changelist, {
            'action': 'download_qr_pack', '_selected_action': [c.pk for c in certs],
        })
        self.assertEqual(response.status_code, 200)
        archive = zipfile.ZipFile(io.BytesIO(response.content))
        self.assertEqual(len(archive.namelist()), 3)
        for cert in certs:
            self.assertIn(f'{cert.serial}.svg', archive.namelist())

    def test_revoke_requires_confirmation_and_a_reason(self):
        cert = make_certificate(self.cohort)

        # Step 1: the action renders a confirmation page rather than revoking.
        response = self.client.post(self.changelist, {
            'action': 'revoke_selected', '_selected_action': [cert.pk],
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Revoke')
        cert.refresh_from_db()
        self.assertEqual(cert.status, Certificate.Status.ISSUED)

        # Step 2: confirming without a reason must not revoke.
        self.client.post(self.changelist, {
            'action': 'revoke_selected', '_selected_action': [cert.pk],
            'confirm_revoke': '1', 'reason': '',
        })
        cert.refresh_from_db()
        self.assertEqual(cert.status, Certificate.Status.ISSUED)

        # Step 3: with a reason it revokes and records who did it.
        self.client.post(self.changelist, {
            'action': 'revoke_selected', '_selected_action': [cert.pk],
            'confirm_revoke': '1', 'reason': 'Issued in error',
            'public_note': 'Reissued as DIDA-IDI-2026-00612',
        })
        cert.refresh_from_db()
        self.assertEqual(cert.status, Certificate.Status.REVOKED)
        self.assertIsNotNone(cert.revoked_at)
        self.assertEqual(cert.revoked_by, self.superuser)
        self.assertEqual(cert.revocation_reason, 'Issued in error')
        self.assertTrue(
            CertificateAuditEvent.objects.filter(
                certificate=cert, action=CertificateAuditEvent.Action.REVOKED
            ).exists()
        )

    def test_issuing_a_draft_records_an_audit_event(self):
        draft = make_certificate(self.cohort, status=Certificate.Status.DRAFT)
        self.client.post(self.changelist, {
            'action': 'mark_as_issued', '_selected_action': [draft.pk],
        })
        draft.refresh_from_db()
        self.assertEqual(draft.status, Certificate.Status.ISSUED)
        self.assertIsNotNone(draft.issued_at)
        self.assertTrue(
            CertificateAuditEvent.objects.filter(
                certificate=draft, action=CertificateAuditEvent.Action.ISSUED
            ).exists()
        )


@isolated_cache
class RegistrarGroupTests(TestCase):
    def test_group_grants_credentials_but_not_home(self):
        call_command('create_registrar_group', verbosity=0)
        from django.contrib.auth.models import Group
        group = Group.objects.get(name='Registrar')

        codenames = set(group.permissions.values_list('codename', flat=True))
        self.assertIn('add_certificate', codenames)
        self.assertIn('change_cohort', codenames)
        self.assertIn('view_certificatescan', codenames)
        self.assertNotIn('change_certificatescan', codenames)

        app_labels = set(
            group.permissions.values_list('content_type__app_label', flat=True)
        )
        self.assertEqual(
            app_labels, {'credentials'},
            'Registrar group grants permissions outside the credentials app',
        )
