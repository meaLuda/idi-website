from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Program, Project, TeamMember


class HttpsSitemap(Sitemap):
    """Base class forcing https in <loc>.

    Django's Sitemap defaults to http, and the site is https-only in production
    (SECURE_SSL_REDIRECT), so the default emitted URLs that immediately redirect.
    """

    protocol = 'https'


class StaticSitemap(HttpsSitemap):
    """Every public page that is not backed by a model.

    This previously listed only four URL names, so roughly a dozen real,
    crawlable pages -- every practice page, services, contact, the case-studies
    index and the civic-innovation fellowship -- were absent from the sitemap.
    """

    changefreq = "weekly"

    def items(self):
        return [
            'home:lander',
            'home:did-academy',
            'home:civic_innovation_fellowship',
            'home:projects_list',
            'home:case_studies_list',
            'home:team_list',
            'home:services',
            'home:contact',
            'home:privacy_policy',
            'home:terms',
            'home:accessibility',
            'home:governance_public_service_delivery',
            'home:responsible_sovereign_ai',
            'home:community_public_service_delivery',
            'home:food_systems_health_practice',
            'home:sustainability_practice',
            'home:venture_building',
        ]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        if item == 'home:lander':
            return 1.0
        if item in {'home:did-academy', 'home:projects_list', 'home:case_studies_list'}:
            return 0.9
        return 0.7


class ProjectSitemap(HttpsSitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Project.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('home:project_detail', args=[obj.slug])


class ProgramSitemap(HttpsSitemap):
    """DIDA programme pages.

    These were routed and rendering but appeared in no sitemap at all.
    """

    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return Program.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('home:program_detail', args=[obj.slug])


class CaseStudySitemap(HttpsSitemap):
    """Case studies.

    These live in a Python list in views.py rather than the database, so there is
    no trustworthy modification date. lastmod is deliberately omitted rather than
    invented -- Google discounts a lastmod it cannot trust.
    """

    changefreq = "yearly"
    priority = 0.8

    def items(self):
        # Imported here to avoid a circular import at module load.
        from .views import CASE_STUDIES

        # power-to-youth and be-green are served by project_detail and are already
        # covered by ProjectSitemap; the rest resolve through case_study_detail.
        redirected = {'power-to-youth', 'be-green', 'kenyas-ai-opportunities-plan-action-lab'}
        return [cs['slug'] for cs in CASE_STUDIES if cs['slug'] not in redirected]

    def location(self, slug):
        return reverse('home:case_study_detail', args=[slug])


class TeamMemberSitemap(HttpsSitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return TeamMember.objects.all()

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('home:team_member_detail', args=[obj.slug])
