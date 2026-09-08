"""Error-page tests.

All four handlers previously rendered 404.html with 404 copy and an
"index, follow" robots tag inherited from meta_tags.html.
"""

from django.test import TestCase


class ErrorHandlerTests(TestCase):
    def test_404_is_noindex_and_says_not_found(self):
        response = self.client.get('/this-page-does-not-exist/')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'noindex, nofollow', status_code=404)
        self.assertNotContains(response, 'index, follow, max-image-preview', status_code=404)
        self.assertContains(response, 'Page not found', status_code=404)

    def test_500_template_is_self_contained(self):
        """It must not depend on base.html, static files or context processors."""
        from django.template.loader import render_to_string
        html = render_to_string('500.html', {})
        self.assertIn('Something went wrong', html)
        self.assertIn('noindex', html)
        for forbidden in ('{% ', '{{ ', 'static/'):
            self.assertNotIn(forbidden, html)

    def test_500_view_renders_without_a_request_context(self):
        from apps.home.views import custom_server_error
        response = custom_server_error(None)
        self.assertEqual(response.status_code, 500)
        self.assertIn(b'Something went wrong', response.content)

    def test_403_and_400_have_their_own_copy(self):
        from apps.home.views import custom_bad_request, custom_permission_denied
        from django.test import RequestFactory
        request = RequestFactory().get('/')

        forbidden = custom_permission_denied(request, Exception())
        self.assertEqual(forbidden.status_code, 403)
        self.assertIn(b'do not have access', forbidden.content)

        bad = custom_bad_request(request, Exception())
        self.assertEqual(bad.status_code, 400)
        self.assertIn(b'could not be processed', bad.content)
