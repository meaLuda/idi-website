"""Scan-logging tests.

Three properties matter more than the analytics themselves: verification must
survive a logging failure, no raw IP may ever be stored, and link-preview bots
must not be counted as people.
"""

import datetime
from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.credentials import scans
from apps.credentials.models import Certificate, CertificateScan
from apps.credentials.tests.test_models import make_certificate, make_cohort
from apps.credentials.tests.utils import isolated_cache

REAL_CLIENT_IP = '41.90.1.1'
SPOOFED_IP = '6.6.6.6'
PROXY_IP = '172.18.0.2'


@isolated_cache
class ClientIpTests(TestCase):
    def _request(self, **meta):
        from django.test import RequestFactory
        return RequestFactory().get('/verify/', **meta)

    def test_uses_remote_addr_when_no_proxy_header(self):
        request = self._request(REMOTE_ADDR=REAL_CLIENT_IP)
        self.assertEqual(scans.client_ip(request), REAL_CLIENT_IP)

    def test_takes_the_last_forwarded_entry_not_the_first(self):
        """Regression: split(',')[0] would trust a client-supplied value.

        Traefik appends the real client to X-Forwarded-For, so anything to the
        left of the last entry was supplied by the caller and must be ignored.
        """
        request = self._request(
            HTTP_X_FORWARDED_FOR=f'{SPOOFED_IP}, {REAL_CLIENT_IP}',
            REMOTE_ADDR=PROXY_IP,
        )
        self.assertEqual(scans.client_ip(request), REAL_CLIENT_IP)
        self.assertNotEqual(scans.client_ip(request), SPOOFED_IP)

    def test_falls_back_when_the_header_is_garbage(self):
        request = self._request(
            HTTP_X_FORWARDED_FOR='not-an-ip', REMOTE_ADDR=REAL_CLIENT_IP,
        )
        self.assertEqual(scans.client_ip(request), REAL_CLIENT_IP)

    def test_returns_empty_when_nothing_is_resolvable(self):
        request = self._request(REMOTE_ADDR='')
        self.assertEqual(scans.client_ip(request), '')

    def test_ipv6_is_accepted(self):
        request = self._request(REMOTE_ADDR='2001:db8::1')
        self.assertEqual(scans.client_ip(request), '2001:db8::1')


@override_settings(SCAN_IP_SALT='test-salt')
@isolated_cache
class IpHashTests(TestCase):
    def test_hash_is_not_reversible_to_the_input(self):
        digest = scans.hash_ip(REAL_CLIENT_IP)
        self.assertNotIn(REAL_CLIENT_IP, digest)
        self.assertEqual(len(digest), 64)

    def test_hash_differs_across_days(self):
        """Date bucketing keeps identities unlinkable over time."""
        a = scans.hash_ip(REAL_CLIENT_IP, datetime.date(2026, 9, 7))
        b = scans.hash_ip(REAL_CLIENT_IP, datetime.date(2026, 9, 8))
        self.assertNotEqual(a, b)

    def test_hash_changes_when_the_salt_changes(self):
        day = datetime.date(2026, 9, 7)
        a = scans.hash_ip(REAL_CLIENT_IP, day)
        with override_settings(SCAN_IP_SALT='a-different-salt'):
            b = scans.hash_ip(REAL_CLIENT_IP, day)
        self.assertNotEqual(a, b, 'salt is not actually being used')

    def test_empty_ip_hashes_to_empty(self):
        self.assertEqual(scans.hash_ip(''), '')


@isolated_cache
class UserAgentTests(TestCase):
    def test_whatsapp_is_a_bot(self):
        is_bot, family = scans.classify_user_agent('WhatsApp/2.23.20.0')
        self.assertTrue(is_bot)
        self.assertEqual(family, 'whatsapp')

    def test_common_unfurlers_are_bots(self):
        for ua in (
            'Slackbot-LinkExpanding 1.0', 'TelegramBot (like TwitterBot)',
            'facebookexternalhit/1.1', 'LinkedInBot/1.0', 'Twitterbot/1.0',
            'Discordbot/2.0', 'python-requests/2.31.0', 'curl/8.4.0',
        ):
            self.assertTrue(scans.classify_user_agent(ua)[0], f'{ua} not flagged')

    def test_absent_user_agent_is_treated_as_a_bot(self):
        self.assertTrue(scans.classify_user_agent('')[0])

    def test_real_browsers_are_not_bots(self):
        for ua in (
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
            'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/120',
        ):
            self.assertFalse(scans.classify_user_agent(ua)[0], f'{ua} wrongly flagged')


@override_settings(SCAN_IP_SALT='test-salt')
@isolated_cache
class ScanLoggingTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.cert = make_certificate(make_cohort())
        self.url = f'/verify/{self.cert.token}/'
        self.browser = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)'

    def test_a_valid_lookup_creates_one_scan_row(self):
        self.client.get(self.url, HTTP_USER_AGENT=self.browser, REMOTE_ADDR=REAL_CLIENT_IP)
        scan = CertificateScan.objects.get()
        self.assertEqual(scan.certificate, self.cert)
        self.assertEqual(scan.outcome, CertificateScan.Outcome.VALID)
        self.assertEqual(scan.certificate_serial, self.cert.serial)

    def test_no_raw_ip_is_stored_in_any_column(self):
        """The Data Protection Act test. Assert explicitly, on every field."""
        self.client.get(self.url, HTTP_USER_AGENT=self.browser, REMOTE_ADDR=REAL_CLIENT_IP)
        scan = CertificateScan.objects.get()
        for field in scan._meta.get_fields():
            if not hasattr(field, 'attname'):
                continue
            value = getattr(scan, field.attname, None)
            if isinstance(value, str):
                self.assertNotIn(
                    REAL_CLIENT_IP, value,
                    f'raw IP address leaked into CertificateScan.{field.attname}',
                )

    def test_raw_user_agent_is_not_stored(self):
        self.client.get(self.url, HTTP_USER_AGENT=self.browser, REMOTE_ADDR=REAL_CLIENT_IP)
        scan = CertificateScan.objects.get()
        self.assertNotIn('iPhone', scan.ua_hash)
        self.assertEqual(scan.ua_family, 'ios')

    def test_repeat_visit_same_day_increments_instead_of_adding_a_row(self):
        for _ in range(3):
            self.client.get(self.url, HTTP_USER_AGENT=self.browser, REMOTE_ADDR=REAL_CLIENT_IP)
        self.assertEqual(CertificateScan.objects.count(), 1)
        self.assertEqual(CertificateScan.objects.get().hit_count, 3)

    def test_scan_count_counts_the_person_once(self):
        for _ in range(3):
            self.client.get(self.url, HTTP_USER_AGENT=self.browser, REMOTE_ADDR=REAL_CLIENT_IP)
        self.cert.refresh_from_db()
        self.assertEqual(self.cert.scan_count, 1)

    def test_a_different_visitor_creates_a_second_row(self):
        self.client.get(self.url, HTTP_USER_AGENT=self.browser, REMOTE_ADDR=REAL_CLIENT_IP)
        self.client.get(self.url, HTTP_USER_AGENT=self.browser, REMOTE_ADDR='197.232.1.1')
        self.assertEqual(CertificateScan.objects.count(), 2)
        self.cert.refresh_from_db()
        self.assertEqual(self.cert.scan_count, 2)

    def test_whatsapp_unfurl_is_recorded_but_not_counted(self):
        self.client.get(self.url, HTTP_USER_AGENT='WhatsApp/2.23', REMOTE_ADDR=REAL_CLIENT_IP)
        scan = CertificateScan.objects.get()
        self.assertTrue(scan.is_bot)
        self.cert.refresh_from_db()
        self.assertEqual(
            self.cert.scan_count, 0,
            'a link-preview fetch was counted as a human verification',
        )

    def test_first_and_last_scanned_at_are_tracked(self):
        self.client.get(self.url, HTTP_USER_AGENT=self.browser, REMOTE_ADDR=REAL_CLIENT_IP)
        self.cert.refresh_from_db()
        self.assertIsNotNone(self.cert.first_scanned_at)
        self.assertIsNotNone(self.cert.last_scanned_at)

    def test_unknown_code_is_logged_with_no_certificate(self):
        from apps.credentials import tokens
        self.client.get(f'/verify/{tokens.generate_code()}/', REMOTE_ADDR=REAL_CLIENT_IP,
                        HTTP_USER_AGENT=self.browser)
        scan = CertificateScan.objects.get()
        self.assertIsNone(scan.certificate)
        self.assertEqual(scan.outcome, CertificateScan.Outcome.NOT_FOUND)

    def test_malformed_code_writes_no_row_at_all(self):
        """The checksum gate exists so brute force cannot grow this table."""
        self.client.get('/verify/AAAAAAAAAAAA/', REMOTE_ADDR=REAL_CLIENT_IP,
                        HTTP_USER_AGENT=self.browser)
        self.assertEqual(CertificateScan.objects.count(), 0)

    def test_referer_stores_host_only(self):
        self.client.get(
            self.url, HTTP_USER_AGENT=self.browser, REMOTE_ADDR=REAL_CLIENT_IP,
            HTTP_REFERER='https://mail.example.com/inbox?token=secret&id=42',
        )
        scan = CertificateScan.objects.get()
        self.assertEqual(scan.referer_host, 'mail.example.com')
        self.assertNotIn('secret', scan.referer_host)

    def test_verification_still_works_when_logging_fails(self):
        """The single most important test here.

        A scan-log failure must degrade to a log line, never to a broken
        verification page.
        """
        with mock.patch(
            'apps.credentials.scans._log_scan', side_effect=RuntimeError('db is down')
        ):
            response = self.client.get(
                self.url, HTTP_USER_AGENT=self.browser, REMOTE_ADDR=REAL_CLIENT_IP,
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ada Kimani')
        self.assertEqual(CertificateScan.objects.count(), 0)


@isolated_cache
class PurgeCommandTests(TestCase):
    def _scan(self, outcome, days_ago, certificate=None):
        return CertificateScan.objects.create(
            certificate=certificate,
            outcome=outcome,
            scanned_at=timezone.now() - datetime.timedelta(days=days_ago),
            dedupe_key=f'{outcome}-{days_ago}-{certificate.pk if certificate else 0}',
        )

    def test_old_misses_go_sooner_than_old_hits(self):
        from django.core.management import call_command
        cert = make_certificate(make_cohort())
        self._scan(CertificateScan.Outcome.NOT_FOUND, 60)
        self._scan(CertificateScan.Outcome.VALID, 60, cert)
        self._scan(CertificateScan.Outcome.NOT_FOUND, 5)

        call_command('purge_scan_logs', verbosity=0)

        remaining = set(CertificateScan.objects.values_list('outcome', flat=True))
        self.assertEqual(CertificateScan.objects.count(), 2)
        self.assertIn(CertificateScan.Outcome.VALID, remaining)

    def test_dry_run_deletes_nothing(self):
        from django.core.management import call_command
        self._scan(CertificateScan.Outcome.NOT_FOUND, 60)
        call_command('purge_scan_logs', dry_run=True, verbosity=0)
        self.assertEqual(CertificateScan.objects.count(), 1)

    def test_certificate_counters_survive_a_purge(self):
        from django.core.management import call_command
        cert = make_certificate(make_cohort())
        Certificate.objects.filter(pk=cert.pk).update(scan_count=42)
        self._scan(CertificateScan.Outcome.VALID, 400, cert)

        call_command('purge_scan_logs', verbosity=0)

        cert.refresh_from_db()
        self.assertEqual(cert.scan_count, 42)
        self.assertEqual(CertificateScan.objects.count(), 0)
