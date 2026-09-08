"""Sitemap tests.

The sitemap previously listed four static URLs and, because the
django.contrib.sites row was still Django's default, published every entry under
http://example.com/ — a domain the organisation does not own.
"""

import re

from django.contrib.sites.models import Site
from django.test import TestCase


class SitemapTests(TestCase):
    def _locs(self):
        body = self.client.get('/sitemap.xml').content.decode()
        return re.findall(r'<loc>(.*?)</loc>', body)

    def test_the_site_row_is_the_real_domain(self):
        self.assertEqual(Site.objects.get(pk=1).domain, 'idi.africa')

    def test_no_url_points_at_example_com(self):
        self.assertEqual([u for u in self._locs() if 'example.com' in u], [])

    def test_every_url_is_https(self):
        locs = self._locs()
        self.assertTrue(locs)
        for url in locs:
            self.assertTrue(url.startswith('https://'), f'{url} is not https')

    def test_the_main_public_pages_are_listed(self):
        paths = {u.replace('https://idi.africa', '') for u in self._locs()}
        for expected in (
            '/', '/services/', '/contact/', '/case-studies/', '/team/',
            '/governance-public-service-delivery/', '/responsible-sovereign-ai/',
            '/venture-building-innovation-ecosystems/', '/health-practice/',
            '/fellowship/democratic-futures-civic-innovation/',
        ):
            self.assertIn(expected, paths, f'{expected} missing from the sitemap')

    def test_case_studies_are_listed(self):
        paths = [u for u in self._locs() if '/case-studies/' in u]
        # The index plus the individual studies.
        self.assertGreater(len(paths), 5)

    def test_verification_urls_are_never_listed(self):
        for url in self._locs():
            self.assertNotIn('/verify/', url)
            self.assertNotIn('/v/', url)
