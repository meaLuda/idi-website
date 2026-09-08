"""
URL configuration for idi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import cache_control
from django.views.static import serve

# Uploaded media rarely changes; let browsers/CDN cache it for 30 days.
cached_media_serve = cache_control(max_age=2592000, public=True)(serve)
from apps.home.sitemap import (
    CaseStudySitemap,
    ProgramSitemap,
    ProjectSitemap,
    StaticSitemap,
    TeamMemberSitemap,
)
from apps.home.views import custom_bad_request, custom_page_not_found, custom_permission_denied, custom_server_error, llms_txt

# AI answer-engine crawlers we explicitly welcome (GEO). They get the same
# access as everyone else: all public content, nothing under /admin/.
AI_CRAWLERS = [
    "GPTBot", "OAI-SearchBot", "ChatGPT-User",   # OpenAI / ChatGPT
    "ClaudeBot", "Claude-Web", "anthropic-ai",   # Anthropic / Claude
    "PerplexityBot", "Perplexity-User",          # Perplexity
    "Google-Extended", "GoogleOther",            # Gemini / Google AI
    "Applebot-Extended",                         # Apple Intelligence
    "Amazonbot", "Bytespider", "CCBot",          # Amazon, TikTok, Common Crawl
]


# Paths no crawler should index. Defined once and emitted in EVERY user-agent
# block below -- a disallow added only to the "User-agent: *" block does not apply
# to a bot that matches its own more specific block.
#
# /verify/ and /v/ are certificate-verification lookups keyed by a per-recipient
# code: one indexable URL per certificate issued, exposing recipient names in
# search snippets. Crawl exclusion here is a courtesy; the actual guarantee is the
# noindex meta tag and X-Robots-Tag header set by the views themselves, since a
# disallowed-but-linked URL can still surface as a bare result.
DISALLOWED_PATHS = ["/admin/", "/verify/", "/v/"]


@require_GET
def robots_txt(request):
    def block(user_agent):
        lines = [f"User-agent: {user_agent}", "Allow: /"]
        lines += [f"Disallow: {path}" for path in DISALLOWED_PATHS]
        return lines + [""]

    lines = block("*")
    for bot in AI_CRAWLERS:
        lines += block(bot)
    lines += [
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
        f"# LLM-readable summary: {request.build_absolute_uri('/llms.txt')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

admin.site.site_header = "IDI Admin Portal"
admin.site.site_title = "IDI Admin Portal"
admin.site.index_title = "Welcome to IDI Admin Portal"


handler404 = 'apps.home.views.custom_page_not_found'
handler500 = 'apps.home.views.custom_server_error'
handler403 = 'apps.home.views.custom_permission_denied'
handler400 = 'apps.home.views.custom_bad_request'


# Define the sitemaps dictionary
sitemaps = {
    'static': StaticSitemap,
    'projects': ProjectSitemap,
    'programs': ProgramSitemap,
    'case_studies': CaseStudySitemap,
    'team': TeamMemberSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    # Mounted before the home include so /verify/ and /v/ resolve here.
    path('', include('apps.credentials.urls', namespace='credentials')),
    path('', include('apps.home.urls', namespace='home')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    
    # SEO URLs
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('llms.txt', llms_txt, name='llms_txt'),
    
    # THIS IS THE KEY FIX - Always serve media files regardless of DEBUG setting
    path('media/<path:path>', cached_media_serve, {'document_root': settings.MEDIA_ROOT}),
]

# Static files handling
if settings.DEBUG:
    urlpatterns += [
        path('test-404/', lambda request: custom_page_not_found(request, Exception())),
        path('test-500/', lambda request: custom_server_error(request)),
        path('test-403/', lambda request: custom_permission_denied(request, Exception())),
        path('test-400/', lambda request: custom_bad_request(request, Exception())),
    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # In production, make sure we can still serve static files with Django
    # (Although ideally, you'd configure Nginx/Apache to handle this)
    urlpatterns += [
        path('static/<path:path>', serve, {'document_root': settings.STATIC_ROOT}),
    ]