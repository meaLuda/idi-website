"""Case studies as editable content.

Reported by Ryan: "Was trying to update the case studies section, but can't see
it kwa admin. I can only update like 3; FFA, E4impact & MPP." Those three were
Project rows; every other case study was a Python dict in views.py.
"""

from django.contrib.admin.sites import site
from django.test import TestCase

from apps.home.models import CaseStudy, CaseStudyStat


class AdminEditabilityTests(TestCase):
    def test_case_studies_are_registered_in_the_admin(self):
        self.assertIn(CaseStudy, site._registry)

    def test_all_case_studies_are_editable_not_just_three(self):
        self.assertGreaterEqual(
            CaseStudy.objects.count(), 14,
            'the hardcoded case studies were not imported',
        )

    def test_statistics_are_edited_inline(self):
        admin = site._registry[CaseStudy]
        self.assertTrue(any(i.model is CaseStudyStat for i in admin.inlines))

    def test_ordering_and_publishing_are_editable_from_the_list(self):
        admin = site._registry[CaseStudy]
        self.assertIn('order', admin.list_editable)
        self.assertIn('is_published', admin.list_editable)


class ImportedContentTests(TestCase):
    def test_the_reviewed_teasers_were_imported(self):
        cs = CaseStudy.objects.get(slug='be-green')
        self.assertIn('market-ready green businesses', cs.teaser)
        self.assertEqual(cs.partners_text, 'UNICEF · Kenya Girl Guides Association')

    def test_headline_figures_are_imported(self):
        justice = CaseStudy.objects.get(
            slug='access-to-justice-judiciary-of-kenya-kenya-law-action-lab')
        self.assertEqual(
            [(s.value, s.label) for s in justice.headline_stats],
            [('91%', 'faster case research')],
        )

    def test_multi_stat_case_studies_keep_their_order(self):
        cs = CaseStudy.objects.get(slug='transboundary-data-flows-unep-giz-action-lab')
        self.assertEqual(
            [s.value for s in cs.stats.all()], ['5', '119', '16', '<15 min'],
        )


class StatHonestyTests(TestCase):
    """A prevalence figure is not an achievement and must not read as one."""

    def test_fgm_prevalence_is_marked_as_context(self):
        cs = CaseStudy.objects.get(slug='power-to-youth')
        stat = cs.stats.get(value='84%')
        self.assertEqual(stat.kind, CaseStudyStat.Kind.CONTEXT)
        self.assertIn('not a programme result', stat.note)

    def test_context_figures_are_excluded_from_headline_stats(self):
        cs = CaseStudy.objects.get(slug='power-to-youth')
        self.assertNotIn('84%', [s.value for s in cs.headline_stats])

    def test_the_card_labels_context_figures(self):
        html = self.client.get('/case-studies/').content.decode()
        if '84%' in html:
            self.assertIn('Context', html)

    def test_the_unverified_plastics_tonnage_is_not_published(self):
        """12,400t vs 14t in the source profile — withheld pending confirmation."""
        for page in ('', '?page=2', '?page=3'):
            self.assertNotIn(
                '12,400', self.client.get('/case-studies/' + page).content.decode(),
            )


class RenderingTests(TestCase):
    def test_the_listing_renders_from_the_database(self):
        response = self.client.get('/case-studies/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '91%')
        self.assertContains(response, 'UNEP · GIZ · Action Lab')

    def test_every_published_case_study_has_a_working_detail_page(self):
        for cs in CaseStudy.objects.filter(is_published=True):
            with self.subTest(slug=cs.slug):
                response = self.client.get(f'/case-studies/{cs.slug}/')
                self.assertIn(response.status_code, (200, 302))

    def test_unpublishing_removes_it_from_the_listing(self):
        cs = CaseStudy.objects.get(slug='be-green')
        cs.is_published = False
        cs.save()
        for page in ('', '?page=2', '?page=3'):
            self.assertNotIn(
                'Young Green Ventures',
                self.client.get('/case-studies/' + page).content.decode(),
            )

    def test_editing_a_title_changes_the_site(self):
        """The whole point: content changes without a deploy."""
        cs = CaseStudy.objects.get(slug='be-green')
        cs.title = 'BeGreen Africa — Updated In Admin'
        cs.save()
        found = any(
            'Updated In Admin' in self.client.get('/case-studies/' + p).content.decode()
            for p in ('', '?page=2', '?page=3')
        )
        self.assertTrue(found)


class ImagelessCaseStudyTests(TestCase):
    """A case study created in the admin has no image yet.

    Reported from production: a newly created case study 500'd. The detail
    template called {% static cs.hero_image %} on an empty string, and
    ManifestStaticFilesStorage raises ValueError for a missing entry rather than
    returning nothing — taking the whole page down.
    """

    def setUp(self):
        self.cs = CaseStudy.objects.create(
            slug='designing-a-co-innovation-platform-for-nutrition-sensitive-social-protection',
            title='Designing a Co-Innovation Platform for Nutrition-Sensitive Social Protection',
            teaser='A platform for co-designing nutrition-sensitive social protection.',
            is_published=True,
        )

    def test_a_case_study_with_no_image_still_renders(self):
        response = self.client.get(f'/case-studies/{self.cs.slug}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nutrition-Sensitive Social Protection')

    def test_it_shows_a_placeholder_rather_than_a_broken_image(self):
        html = self.client.get(f'/case-studies/{self.cs.slug}/').content.decode()
        self.assertIn('bg-brand-teal-500/10', html)

    def test_it_appears_on_the_listing_without_an_image(self):
        found = any(
            'Nutrition-Sensitive' in self.client.get('/case-studies/' + p).content.decode()
            for p in ('', '?page=2', '?page=3')
        )
        self.assertTrue(found)

    def test_every_case_study_renders_even_with_no_imagery(self):
        """Guards the whole set, not just this one slug."""
        CaseStudy.objects.update(hero_image_static='')
        for cs in CaseStudy.objects.filter(is_published=True):
            with self.subTest(slug=cs.slug):
                response = self.client.get(f'/case-studies/{cs.slug}/')
                self.assertIn(response.status_code, (200, 302))
