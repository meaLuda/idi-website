"""Team display order.

Reported from production: there was no way to control the order team members
appear in. TeamMember was the only content model without an `order` field, so
the page was locked to alphabetical and leadership could not be placed first.
"""

import re

from django.test import TestCase

from apps.home.models import TeamMember


def make_member(name, order=0, **kw):
    return TeamMember.objects.create(
        name=name, position=kw.pop('position', 'Role'), bio='x', order=order, **kw
    )


class OrderingTests(TestCase):
    def setUp(self):
        # Deliberately created so that alphabetical order contradicts `order`.
        make_member('Carol Zulu', order=1)
        make_member('Alice Adams', order=3)
        make_member('Bob Banda', order=2)

    def test_order_field_beats_alphabetical(self):
        self.assertEqual(
            [m.name for m in TeamMember.objects.all()],
            ['Carol Zulu', 'Bob Banda', 'Alice Adams'],
        )

    def test_equal_order_falls_back_to_name(self):
        TeamMember.objects.update(order=0)
        self.assertEqual(
            [m.name for m in TeamMember.objects.all()],
            ['Alice Adams', 'Bob Banda', 'Carol Zulu'],
        )

    def test_the_team_page_renders_in_that_order(self):
        html = self.client.get('/team/').content.decode()
        positions = sorted(
            (html.index(n), n)
            for n in ('Carol Zulu', 'Bob Banda', 'Alice Adams')
        )
        self.assertEqual(
            [n for _, n in positions], ['Carol Zulu', 'Bob Banda', 'Alice Adams'],
        )

    def test_order_is_editable_from_the_admin_list(self):
        from django.contrib.admin.sites import site
        admin = site._registry[TeamMember]
        self.assertIn('order', admin.list_display)
        self.assertIn('order', admin.list_editable)
        # The name must stay the link, or list_editable has nothing to link from.
        self.assertIn('name', admin.list_display_links)


class TeamCardTests(TestCase):
    def test_no_external_image_host_is_requested(self):
        """A missing photo used to pull a stock image from cdn.pixabay.com."""
        make_member('Photoless Person')
        for url in ('/team/', '/'):
            self.assertNotIn('cdn.pixabay', self.client.get(url).content.decode())

    def test_a_member_without_a_photo_gets_a_local_placeholder(self):
        make_member('Photoless Person')
        html = self.client.get('/team/').content.decode()
        self.assertIn('Photoless Person', html)
        self.assertIn('bg-brand-teal-500/10', html)

    def test_member_names_do_not_skip_heading_levels(self):
        make_member('Ada Kimani')
        html = self.client.get('/team/').content.decode()
        levels = [int(m) for m in re.findall(r'<h([1-6])\b', html)]
        self.assertEqual(levels.count(1), 1, 'expected exactly one h1')
        # No jump greater than one level anywhere in the outline.
        for previous, current in zip(levels, levels[1:]):
            self.assertLessEqual(
                current - previous, 1,
                f'heading jumps from h{previous} to h{current}',
            )
