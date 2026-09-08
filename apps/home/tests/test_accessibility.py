"""Accessibility regressions.

These pin the fixes that are easiest to undo accidentally: a template rewrite can
silently drop the skip link, and a copy-paste can reintroduce a div-with-onclick.
"""

import re

from django.test import TestCase


class SkipLinkTests(TestCase):
    def test_every_page_has_a_skip_link_targeting_main(self):
        for url in ('/', '/contact/', '/case-studies/', '/team/', '/fellowship/did-academy/'):
            html = self.client.get(url).content.decode()
            self.assertIn('href="#main-content"', html, f'no skip link on {url}')
            self.assertIn('id="main-content"', html, f'no skip target on {url}')

    def test_the_skip_link_is_the_first_focusable_element(self):
        html = self.client.get('/').content.decode()
        body = html[html.index('<body'):]
        first_link = body.index('<a ')
        first_button = body.index('<button') if '<button' in body else len(body)
        self.assertLess(first_link, first_button)
        self.assertIn('#main-content', body[first_link:first_link + 200])


class LandmarkTests(TestCase):
    def test_the_nav_landmark_is_named(self):
        html = self.client.get('/').content.decode()
        self.assertIn('<nav aria-label="Main"', html)

    def test_main_is_focusable_as_a_skip_target(self):
        html = self.client.get('/').content.decode()
        self.assertIn('id="main-content" tabindex="-1"', html)


class MobileMenuTests(TestCase):
    def test_the_toggle_exposes_its_state(self):
        html = self.client.get('/').content.decode()
        self.assertIn('aria-expanded="false"', html)
        self.assertIn('aria-controls="mobile-menu"', html)

    def test_escape_and_focus_handling_are_wired(self):
        html = self.client.get('/').content.decode()
        self.assertIn("e.key === 'Escape'", html)
        self.assertIn('btn.focus()', html)


class InteractiveElementTests(TestCase):
    def test_the_academy_accordion_uses_buttons_not_divs(self):
        html = self.client.get('/fellowship/did-academy/').content.decode()
        self.assertNotIn('onclick="activateAccordionItem', html)
        self.assertIn('<button type="button" class="image-accordion-item', html)
        self.assertIn('aria-pressed=', html)

    def test_no_page_conveys_an_action_with_a_bare_div_onclick(self):
        for url in ('/', '/fellowship/did-academy/', '/case-studies/', '/contact/'):
            html = self.client.get(url).content.decode()
            self.assertNotRegex(
                html, r'<div[^>]*\sonclick=',
                f'{url} has a div with onclick, which is not keyboard operable',
            )


class HeadingTests(TestCase):
    def _headings(self, url):
        html = self.client.get(url).content.decode()
        return re.findall(r'<h([1-6])\b', html)

    def test_key_pages_have_exactly_one_h1(self):
        for url in ('/fellowship/did-academy/',
                    '/fellowship/democratic-futures-civic-innovation/',
                    '/case-studies/', '/contact/', '/team/'):
            levels = self._headings(url)
            self.assertEqual(
                levels.count('1'), 1,
                f'{url} has {levels.count("1")} h1 elements, expected exactly 1',
            )

    def test_the_academy_page_has_a_real_heading_structure(self):
        """It previously had zero heading elements in 470 lines."""
        levels = self._headings('/fellowship/did-academy/')
        self.assertGreaterEqual(len(levels), 5)
        self.assertIn('2', levels)


class DeadLinkTests(TestCase):
    def test_no_page_ships_an_href_hash_placeholder(self):
        for url in ('/', '/contact/', '/case-studies/', '/projects/', '/team/',
                    '/fellowship/did-academy/', '/services/',
                    '/governance-public-service-delivery/', '/responsible-sovereign-ai/'):
            html = self.client.get(url).content.decode()
            self.assertNotIn('href="#"', html, f'{url} still contains a dead link')

    def test_the_policy_pages_exist_and_are_linked(self):
        html = self.client.get('/').content.decode()
        for path in ('/privacy-policy/', '/terms/', '/accessibility/'):
            self.assertIn(path, html, f'{path} not linked from the footer')
            self.assertEqual(self.client.get(path).status_code, 200)


class ImageTests(TestCase):
    def test_images_declare_intrinsic_dimensions(self):
        """Missing width/height is the main source of layout shift here."""
        html = self.client.get('/').content.decode()
        imgs = re.findall(r'<img\b[^>]*>', html)
        self.assertTrue(imgs)
        missing = [t for t in imgs if 'width=' not in t or 'height=' not in t]
        self.assertLessEqual(
            len(missing), len(imgs) * 0.2,
            f'{len(missing)} of {len(imgs)} images on / lack width/height',
        )

    def test_every_image_has_an_alt_attribute(self):
        for url in ('/', '/team/', '/case-studies/'):
            for tag in re.findall(r'<img\b[^>]*>', self.client.get(url).content.decode()):
                self.assertIn('alt=', tag, f'image without alt on {url}: {tag[:80]}')
