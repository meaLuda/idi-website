"""Template hygiene checks.

Django's ``{# ... #}`` comment syntax is SINGLE-LINE only. A multi-line one is
not stripped and renders as visible page text. This has slipped through by hand
three times in this codebase, so it is asserted here instead.
"""

import pathlib
import re

from django.test import SimpleTestCase, TestCase

TEMPLATE_ROOT = pathlib.Path(__file__).resolve().parents[3] / 'templates'

# {# ... #} where the opening and closing markers are on different lines.
MULTILINE_HASH_COMMENT = re.compile(r'\{#(?:(?!#\})[^\n])*\n', re.M)


class TemplateCommentSyntaxTests(SimpleTestCase):
    def test_no_multiline_hash_comments(self):
        """A multi-line {# #} renders to the page instead of being stripped."""
        offenders = []
        for path in sorted(TEMPLATE_ROOT.rglob('*.html')):
            for match in MULTILINE_HASH_COMMENT.finditer(path.read_text()):
                line = path.read_text()[:match.start()].count('\n') + 1
                offenders.append(f'{path.relative_to(TEMPLATE_ROOT)}:{line}')
        self.assertEqual(
            offenders, [],
            'Multi-line {# #} comments leak into rendered output. '
            'Use {% comment %}...{% endcomment %} instead. Found at: '
            + ', '.join(offenders),
        )


class RenderedCommentLeakTests(TestCase):
    """Belt and braces: fetch real pages and look for comment prose in the body."""

    # Wording that only ever appears inside explanatory comments.
    LEAK_MARKERS = (
        'screen reader announces',
        'Removed rather than',
        'placeholder article',
        'renders to the page',
        'was removed. Its three selects',
    )

    def test_pages_do_not_render_comment_prose(self):
        for url in ('/', '/contact/', '/projects/', '/case-studies/',
                    '/fellowship/did-academy/', '/verify/', '/admin/login/'):
            html = self.client.get(url).content.decode()
            for marker in self.LEAK_MARKERS:
                self.assertNotIn(
                    marker, html,
                    f'comment text leaked into {url}: {marker!r}',
                )
