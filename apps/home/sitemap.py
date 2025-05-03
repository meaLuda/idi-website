from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Project, TeamMember


class StaticSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return ['home:lander', 'home:did-fellowships', 'home:decision-intelligence-design-academy', 
                'home:projects_list', 'home:team_list']

    def location(self, item):
        return reverse(item)


class ProjectSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Project.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('home:project_detail', args=[obj.slug])


class TeamMemberSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return TeamMember.objects.all()

    def lastmod(self, obj):
        return obj.create_at

    def location(self, obj):
        return reverse('home:team_member_detail', args=[obj.slug])