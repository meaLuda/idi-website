"""Crawler-exclusion guarantees for the verification pages.

A verification URL is a lookup keyed to one recipient. Indexing it would put
graduates' names into search snippets and create one indexable URL per
certificate issued.
"""

from django.test import TestCase

from apps.credentials import tokens
from apps.credentials.tests.test_models import make_certificate, make_cohort
from apps.credentials.tests.utils import isolated_cache


@isolated_cache
class RobotsTests(TestCase):
    def test_verify_is_disallowed_in_every_user_agent_block(self):
        """A disallow in the wildcard block does not apply to a bot with its own."""
        body = self.client.get('/robots.txt').content.decode()
        blocks = [b for b in body.split('User-agent:') if b.strip()]
        self.assertGreater(len(blocks), 5, 'expected the AI-crawler blocks to be present')
        for block in blocks:
            self.assertIn('Disallow: /verify/', block)
            self.assertIn('Disallow: /v/', block)
            self.assertIn('Disallow: /admin/', block)

    def test_sitemap_contains_no_verification_urls(self):
        make_certificate(make_cohort())
        body = self.client.get('/sitemap.xml').content.decode()
        self.assertNotIn('/verify/', body)
        self.assertNotIn('/v/', body)


@isolated_cache
class NoindexTests(TestCase):
    def setUp(self):
        self.cert = make_certificate(make_cohort())

    def test_every_verification_response_is_noindex(self):
        cases = [
            f'/verify/{self.cert.token}/',
            f'/v/{self.cert.token}',
            f'/verify/{tokens.generate_code()}/',
            '/verify/',
        ]
        for url in cases:
            response = self.client.get(url)
            self.assertEqual(
                response['X-Robots-Tag'], 'noindex, nofollow, noarchive',
                f'missing X-Robots-Tag header on {url}',
            )
            self.assertContains(
                response, 'noindex, nofollow, noarchive',
                status_code=response.status_code,
                msg_prefix=f'missing noindex meta tag on {url}',
            )

    def test_exactly_one_robots_meta_tag_is_emitted(self):
        """Two conflicting robots meta tags are undefined behaviour across engines."""
        html = self.client.get(f'/verify/{self.cert.token}/').content.decode()
        self.assertEqual(html.count('name="robots"'), 1)

    def test_ordinary_pages_remain_indexable(self):
        html = self.client.get('/').content.decode()
        self.assertIn('index, follow', html)
        self.assertNotIn('noindex', html)
