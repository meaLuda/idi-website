"""Archived-PDF tests: validation, fingerprinting, and non-exposure."""

import hashlib

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.credentials.models import Certificate
from apps.credentials.storage import certificate_pdf_path
from apps.credentials.tests.test_models import make_certificate, make_cohort
from apps.credentials.tests.utils import isolated_cache
from apps.credentials.validators import (
    MAX_PDF_BYTES,
    PdfMagicBytesValidator,
    validate_pdf_size,
)

REAL_PDF = b'%PDF-1.7\n1 0 obj\n<<>>\nendobj\ntrailer\n%%EOF\n'


@isolated_cache
class ValidatorTests(TestCase):
    def test_a_non_pdf_named_pdf_is_rejected(self):
        """An extension check alone is trivially bypassed."""
        fake = SimpleUploadedFile('certificate.pdf', b'MZ\x90\x00 this is an exe', 'application/pdf')
        with self.assertRaises(ValidationError):
            PdfMagicBytesValidator()(fake)

    def test_a_real_pdf_passes(self):
        good = SimpleUploadedFile('certificate.pdf', REAL_PDF, 'application/pdf')
        PdfMagicBytesValidator()(good)  # must not raise

    def test_the_validator_rewinds_the_file(self):
        """Forgetting seek(0) silently truncates the stored file."""
        upload = SimpleUploadedFile('certificate.pdf', REAL_PDF, 'application/pdf')
        PdfMagicBytesValidator()(upload)
        upload.seek(0)
        self.assertEqual(upload.read(), REAL_PDF)

    def test_oversized_files_are_rejected(self):
        big = SimpleUploadedFile('big.pdf', b'%PDF-' + b'0' * MAX_PDF_BYTES, 'application/pdf')
        with self.assertRaises(ValidationError):
            validate_pdf_size(big)

    def test_files_within_the_cap_pass(self):
        ok = SimpleUploadedFile('ok.pdf', REAL_PDF, 'application/pdf')
        validate_pdf_size(ok)


@isolated_cache
class StoragePathTests(TestCase):
    def test_the_client_filename_is_discarded(self):
        cert = make_certificate(make_cohort())
        path = certificate_pdf_path(cert, '../../etc/passwd.pdf')
        self.assertNotIn('passwd', path)
        self.assertNotIn('..', path)
        self.assertTrue(path.endswith('.pdf'))

    def test_the_path_is_not_derivable_from_the_serial(self):
        cert = make_certificate(make_cohort())
        path = certificate_pdf_path(cert, 'x.pdf')
        self.assertNotIn(cert.serial, path)

    def test_two_paths_for_the_same_certificate_differ(self):
        cert = make_certificate(make_cohort())
        self.assertNotEqual(
            certificate_pdf_path(cert, 'a.pdf'), certificate_pdf_path(cert, 'a.pdf')
        )


@isolated_cache
class FingerprintTests(TestCase):
    def test_sha256_and_size_are_recorded_on_upload(self):
        cert = make_certificate(make_cohort(), status=Certificate.Status.DRAFT)
        cert.pdf = SimpleUploadedFile('c.pdf', REAL_PDF, 'application/pdf')
        cert.save()
        cert.refresh_from_db()
        self.assertEqual(cert.pdf_sha256, hashlib.sha256(REAL_PDF).hexdigest())
        self.assertEqual(cert.pdf_size, len(REAL_PDF))
        cert.pdf.delete(save=False)

    def test_the_stored_file_is_not_truncated(self):
        cert = make_certificate(make_cohort(), status=Certificate.Status.DRAFT)
        cert.pdf = SimpleUploadedFile('c.pdf', REAL_PDF, 'application/pdf')
        cert.save()
        cert.refresh_from_db()
        cert.pdf.open('rb')
        self.assertEqual(cert.pdf.read(), REAL_PDF)
        cert.pdf.close()
        cert.pdf.delete(save=False)


@isolated_cache
class PublicExposureTests(TestCase):
    def test_the_pdf_is_never_linked_from_the_public_page(self):
        cert = make_certificate(make_cohort(), status=Certificate.Status.DRAFT)
        cert.pdf = SimpleUploadedFile('c.pdf', REAL_PDF, 'application/pdf')
        cert.save()
        Certificate.objects.filter(pk=cert.pk).update(status=Certificate.Status.ISSUED)

        response = self.client.get(f'/verify/{cert.token}/')
        body = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('.pdf', body)
        self.assertNotIn(cert.pdf_sha256, body)
        cert.pdf.delete(save=False)

    @override_settings(USE_S3=False)
    def test_local_fallback_stays_outside_media_root(self):
        """Local dev must not drop PDFs into the publicly-served media tree."""
        from django.conf import settings
        from apps.credentials.storage import certificate_storage
        storage = certificate_storage()
        location = getattr(storage, 'location', '')
        self.assertNotIn(str(settings.MEDIA_ROOT), str(location))
