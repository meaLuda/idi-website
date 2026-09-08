"""Rate-limit tests.

The throttle is a courtesy, not the security control -- the code's 55 bits of
entropy are. That is precisely why failing open is correct, and why it is tested.
"""

from unittest import mock

from django.core.cache import cache
from django.test import TestCase

from apps.credentials import throttle, tokens
from apps.credentials.models import Certificate, CertificateScan
from apps.credentials.tests.test_models import make_certificate, make_cohort
from apps.credentials.tests.utils import isolated_cache

IP_A = '41.90.1.1'
IP_B = '197.232.1.1'
BROWSER = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)'


@isolated_cache
class ThrottleUnitTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_requests_are_allowed_up_to_the_limit(self):
        limit, _ = throttle.LIMIT_FORM
        for i in range(limit):
            allowed, _ = throttle.check_form('ident-a')
            self.assertTrue(allowed, f'blocked at request {i + 1} of {limit}')

    def test_the_request_after_the_limit_is_blocked(self):
        limit, window = throttle.LIMIT_FORM
        for _ in range(limit):
            throttle.check_form('ident-a')
        allowed, retry_after = throttle.check_form('ident-a')
        self.assertFalse(allowed)
        self.assertEqual(retry_after, window)

    def test_identities_have_independent_budgets(self):
        limit, _ = throttle.LIMIT_FORM
        for _ in range(limit + 1):
            throttle.check_form('ident-a')
        allowed, _ = throttle.check_form('ident-b')
        self.assertTrue(allowed, 'one abuser exhausted another visitor\'s budget')

    def test_empty_identity_is_never_throttled(self):
        """An unresolvable IP must not throttle every anonymous caller together."""
        for _ in range(throttle.LIMIT_FORM[0] * 3):
            allowed, _ = throttle.check_form('')
            self.assertTrue(allowed)

    def test_failures_have_their_own_budget(self):
        limit, _ = throttle.LIMIT_FAILURES
        for _ in range(limit):
            allowed, _ = throttle.register_failure('ident-a')
            self.assertTrue(allowed)
        allowed, retry_after = throttle.register_failure('ident-a')
        self.assertFalse(allowed)
        self.assertGreater(retry_after, 0)

    def test_it_fails_open_when_the_cache_is_unavailable(self):
        """A verify page dark because Redis restarted is worse than an unthrottled one."""
        with mock.patch(
            'apps.credentials.throttle.cache.add', side_effect=ConnectionError('no cache')
        ):
            allowed, retry_after = throttle.check_lookup('ident-a')
        self.assertTrue(allowed)
        self.assertEqual(retry_after, 0)


@isolated_cache
class ThrottleViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.cert = make_certificate(make_cohort())

    def test_repeated_failed_lookups_eventually_return_429(self):
        limit, _ = throttle.LIMIT_FAILURES
        last = None
        for _ in range(limit + 2):
            last = self.client.get(
                f'/verify/{tokens.generate_code()}/',
                REMOTE_ADDR=IP_A, HTTP_USER_AGENT=BROWSER,
            )
        self.assertEqual(last.status_code, 429)
        self.assertIn('Retry-After', last)
        self.assertTemplateUsed(last, 'credentials/verify_throttled.html')

    def test_successful_lookups_do_not_consume_the_failure_budget(self):
        """A legitimate visitor must never throttle themselves."""
        for _ in range(throttle.LIMIT_FAILURES[0] + 5):
            response = self.client.get(
                f'/verify/{self.cert.token}/', REMOTE_ADDR=IP_A, HTTP_USER_AGENT=BROWSER,
            )
            self.assertEqual(response.status_code, 200)

    def test_one_abuser_does_not_block_another_visitor(self):
        for _ in range(throttle.LIMIT_FAILURES[0] + 2):
            self.client.get(
                f'/verify/{tokens.generate_code()}/',
                REMOTE_ADDR=IP_A, HTTP_USER_AGENT=BROWSER,
            )
        response = self.client.get(
            f'/verify/{self.cert.token}/', REMOTE_ADDR=IP_B, HTTP_USER_AGENT=BROWSER,
        )
        self.assertEqual(response.status_code, 200)

    def test_a_certificate_cannot_be_locked_out_by_hammering_its_code(self):
        """The throttle is keyed on the caller, never on the token."""
        for _ in range(throttle.LIMIT_FAILURES[0] + 2):
            self.client.get(
                f'/verify/{self.cert.token}/', REMOTE_ADDR=IP_A, HTTP_USER_AGENT=BROWSER,
            )
        response = self.client.get(
            f'/verify/{self.cert.token}/', REMOTE_ADDR=IP_B, HTTP_USER_AGENT=BROWSER,
        )
        self.assertEqual(response.status_code, 200)

    def test_throttled_response_is_noindex(self):
        for _ in range(throttle.LIMIT_FAILURES[0] + 2):
            last = self.client.get(
                f'/verify/{tokens.generate_code()}/',
                REMOTE_ADDR=IP_A, HTTP_USER_AGENT=BROWSER,
            )
        self.assertEqual(last['X-Robots-Tag'], 'noindex, nofollow, noarchive')
