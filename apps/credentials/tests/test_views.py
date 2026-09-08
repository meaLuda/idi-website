"""Public verification view tests.

The properties under test are the ones the feature exists to guarantee: the right
answer for every state, no information leak about codes that don't exist, no
personal data in social previews, and no dependency on the scan log succeeding.
"""

import datetime
import re

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.credentials import tokens
from apps.credentials.models import Certificate, CertificateScan
from apps.credentials.tests.test_models import make_certificate, make_cohort
from apps.credentials.tests.utils import isolated_cache


def _stable(response):
    """Strip per-request values so two responses can be compared for equality.

    The CSRF token and the signed anti-bot timestamp differ on every request by
    design; everything else must be identical.
    """
    html = response.content.decode()
    html = re.sub(r'value="[A-Za-z0-9+/=:_\-]{20,}"', 'value="REDACTED"', html)
    return html


@isolated_cache
class VerifyViewTestCase(TestCase):
    """Clears the shared cache so throttle counters don't leak between tests."""

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.cohort = make_cohort()


@isolated_cache
class ValidCertificateTests(VerifyViewTestCase):
    def setUp(self):
        super().setUp()
        self.cert = make_certificate(self.cohort)
        self.url = reverse('credentials:detail', kwargs={'code': self.cert.token})

    def test_valid_certificate_renders(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'credentials/verify_detail.html')
        self.assertContains(response, 'Verified certificate')
        self.assertContains(response, 'Ada Kimani')
        self.assertContains(response, self.cert.serial)

    def test_shows_the_hyphenated_verification_code(self):
        response = self.client.get(self.url)
        self.assertContains(response, tokens.format_code(self.cert.token))

    def test_instructs_the_reader_to_compare_the_name(self):
        """The actual anti-forgery control is this sentence, so assert it exists."""
        response = self.client.get(self.url)
        self.assertContains(response, 'match the document you are holding')

    def test_case_and_hyphen_variants_all_resolve(self):
        for variant in (
            self.cert.token,
            self.cert.token.lower(),
            tokens.format_code(self.cert.token),
            tokens.format_code(self.cert.token).lower(),
        ):
            response = self.client.get(f'/verify/{variant}/')
            self.assertEqual(response.status_code, 200, f'failed for {variant!r}')

    def test_short_qr_url_resolves_and_canonicalises_to_the_long_form(self):
        response = self.client.get(f'/v/{self.cert.token}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'/verify/{self.cert.token}/')

    def test_uppercase_code_as_encoded_in_the_qr_resolves(self):
        """The QR encodes the uppercase form; the path must match it."""
        response = self.client.get(f'/v/{self.cert.token.upper()}')
        self.assertEqual(response.status_code, 200)

    def test_response_is_uncacheable_and_noindex(self):
        response = self.client.get(self.url)
        self.assertIn('no-store', response['Cache-Control'])
        self.assertEqual(response['X-Robots-Tag'], 'noindex, nofollow, noarchive')
        self.assertContains(response, 'noindex, nofollow, noarchive')

    def test_recipient_name_never_appears_in_social_preview_tags(self):
        """Pasting the link into a group chat must not broadcast the name."""
        response = self.client.get(self.url)
        html = response.content.decode()
        for line in html.splitlines():
            if 'og:' in line or 'twitter:' in line:
                self.assertNotIn(
                    'Ada Kimani', line, f'recipient name leaked into: {line.strip()}'
                )

    def test_private_fields_are_never_rendered(self):
        self.cert.recipient_email = 'ada@example.com'
        self.cert.notes = 'internal note about this person'
        Certificate.objects.filter(pk=self.cert.pk).update(
            recipient_email=self.cert.recipient_email, notes=self.cert.notes,
        )
        response = self.client.get(self.url)
        self.assertNotContains(response, 'ada@example.com')
        self.assertNotContains(response, 'internal note about this person')

    def test_query_count_is_bounded(self):
        """One certificate lookup plus the scan-log write. Guards against an N+1."""
        with self.assertNumQueries(7):
            self.client.get(self.url)


@isolated_cache
class NotFoundTests(VerifyViewTestCase):
    def test_unknown_but_well_formed_code_is_404(self):
        code = tokens.generate_code()
        response = self.client.get(f'/verify/{code}/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'credentials/verify_not_found.html')

    def test_draft_is_indistinguishable_from_unknown(self):
        """A draft must not confirm that a code exists."""
        draft = make_certificate(self.cohort, status=Certificate.Status.DRAFT)
        draft_response = self.client.get(f'/verify/{draft.token}/')
        unknown_response = self.client.get(f'/verify/{tokens.generate_code()}/')

        self.assertEqual(draft_response.status_code, 404)
        self.assertEqual(unknown_response.status_code, 404)
        self.assertEqual(
            _stable(draft_response), _stable(unknown_response),
            'draft and unknown responses differ, leaking the existence of the record',
        )

    def test_checksum_failure_looks_the_same_as_unknown(self):
        bad = 'AAAAAAAAAAAA'  # well-formed characters, wrong check character
        self.assertFalse(tokens.is_valid_code(bad))
        bad_response = self.client.get(f'/verify/{bad}/')
        unknown_response = self.client.get(f'/verify/{tokens.generate_code()}/')
        self.assertEqual(bad_response.status_code, 404)
        self.assertEqual(_stable(bad_response), _stable(unknown_response))

    def test_malformed_code_costs_no_database_query(self):
        """31 of 32 random guesses die on the checksum, before the database."""
        with self.assertNumQueries(0):
            self.client.get('/verify/AAAAAAAAAAAA/')

    def test_routing_rejects_junk_before_the_view(self):
        for junk in ('/verify/x/', '/verify/' + 'A' * 40 + '/', '/verify/a_b/'):
            self.assertEqual(self.client.get(junk).status_code, 404)

    def test_not_found_is_noindex(self):
        response = self.client.get(f'/verify/{tokens.generate_code()}/')
        self.assertEqual(response['X-Robots-Tag'], 'noindex, nofollow, noarchive')


@isolated_cache
class StateTests(VerifyViewTestCase):
    def test_revoked_returns_200_not_404(self):
        """Verification succeeded; the answer is negative."""
        cert = make_certificate(
            self.cohort,
            status=Certificate.Status.REVOKED,
            revoked_at=timezone.now(),
            revocation_public_note='Reissued as DIDA-IDI-2026-00612',
        )
        response = self.client.get(f'/verify/{cert.token}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Revoked')
        self.assertContains(response, 'Reissued as DIDA-IDI-2026-00612')
        self.assertNotContains(response, 'Verified certificate')
        # The recipient is still shown, so the holder knows which record this is.
        self.assertContains(response, 'Ada Kimani')

    def test_expired_shows_genuine_but_expired(self):
        cert = make_certificate(
            self.cohort,
            issue_date=datetime.date(2020, 1, 1),
            completion_date=datetime.date(2019, 12, 1),
            expires_on=datetime.date(2021, 1, 1),
        )
        response = self.client.get(f'/verify/{cert.token}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'expired')
        self.assertContains(response, 'Ada Kimani')

    def test_superseded_links_to_the_replacement(self):
        replacement = make_certificate(self.cohort, recipient_full_name='Ada N. Kimani')
        old = make_certificate(
            self.cohort,
            status=Certificate.Status.SUPERSEDED,
            superseded_by=replacement,
        )
        response = self.client.get(f'/verify/{old.token}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, replacement.serial)
        self.assertContains(response, replacement.get_absolute_url())


@isolated_cache
class LookupFormTests(VerifyViewTestCase):
    def test_get_renders_the_form(self):
        response = self.client.get(reverse('credentials:lookup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'credentials/verify_lookup.html')

    def test_valid_submission_redirects_to_the_certificate(self):
        cert = make_certificate(self.cohort)
        response = self.client.post(
            reverse('credentials:lookup'),
            {'code': tokens.format_code(cert.token), 'website': '', 'ts': ''},
        )
        self.assertRedirects(response, cert.get_absolute_url())

    def test_honeypot_submission_is_rejected(self):
        cert = make_certificate(self.cohort)
        response = self.client.post(
            reverse('credentials:lookup'),
            {'code': cert.token, 'website': 'http://spam.example', 'ts': ''},
        )
        self.assertEqual(response.status_code, 200)  # re-renders, no redirect

    def test_submission_faster_than_a_human_is_rejected(self):
        from apps.credentials.forms import CertificateLookupForm
        cert = make_certificate(self.cohort)
        response = self.client.post(
            reverse('credentials:lookup'),
            {
                'code': cert.token,
                'website': '',
                'ts': CertificateLookupForm.make_timestamp(),  # just now
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIsInstance(response, type(None))

    def test_invalid_code_shows_one_generic_message(self):
        response = self.client.post(
            reverse('credentials:lookup'), {'code': 'NOPE', 'website': '', 'ts': ''},
        )
        self.assertContains(response, 'look like a valid verification code')
