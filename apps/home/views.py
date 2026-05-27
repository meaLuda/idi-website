from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from django.views.generic import ListView, DetailView
from .models import Project, TeamMember, Testimonial, Program, Partner, Client, HomeStat, ServicePillar

ARTICLE_PAGE_SIZE = 4

# WHERE WE APPLY IT — static content (slug drives the masked tile asset).
PRACTICE_TILES = [
    {"num": "01", "slug": "governance-public-service-delivery", "title": "Governance & Public Service Delivery"},
    {"num": "02", "slug": "responsible-sovereign-ai", "title": "Responsible / Sovereign AI"},
    {"num": "03", "slug": "sustainability-practice", "title": "Sustainability Practice"},
    {"num": "04", "slug": "venture-building-innovation-ecosystems", "title": "Venture Building & Innovation Ecosystems"},
    {"num": "05", "slug": "community-public-service-delivery", "title": "Community & Public Service Delivery"},
    {"num": "06", "slug": "food-systems-health-practice", "title": "Food Systems & Health Practice"},
]


def article_page(page_number):
    """A page of published articles (Projects), newest first."""
    qs = Project.objects.filter(is_active=True).order_by('order', '-created_at')
    return Paginator(qs, ARTICLE_PAGE_SIZE).get_page(page_number)


def articles(request):
    """HTMX endpoint: return one page of article cards."""
    return render(request, 'home/partials/_article_cards.html',
                  {'page': article_page(request.GET.get('page', 1))})

# Create your views here.
def home(request):
    # Optimize queries with select_related and prefetch_related
    team_members = TeamMember.objects.select_related().all()[:6]
    projects = Project.objects.filter(is_active=True).select_related()[:6]
    article_first_page = article_page(1)
    home_stats = HomeStat.objects.filter(is_active=True)
    service_pillars = ServicePillar.objects.filter(is_active=True)
    testimonials = Testimonial.objects.filter(is_active=True).select_related()
    partners = Partner.objects.filter(is_active=True, is_featured=True).select_related().order_by('order')
    clients = Client.objects.filter(is_active=True, is_featured=True).select_related().order_by('order')
    
    # SEO metadata
    context = {
        'team_members': team_members,
        'projects': projects,
        'article_first_page': article_first_page,
        'home_stats': home_stats,
        'service_pillars': service_pillars,
        'practices': PRACTICE_TILES,
        'testimonials': testimonials,
        'partners': partners,
        'clients': clients,
        'page_title': 'Home',
        'page_description': 'IDI Africa pioneers Decision Intelligence Design in Africa, transforming complexity into actionable solutions through our innovative fellowship programs and impactful initiatives.',
        'page_keywords': 'Decision Intelligence, Design Thinking, AI, Innovation, Fellowship, Africa, Kenya',
    }
    return render(request, "home/index.html", context)


# def fellowships(request):
#     # SEO metadata
#     context = {
#         'page_title': 'Decision Intelligence Design Fellowships',
#         'page_description': 'Transform complexity into actionable solutions through our immersive fellowship programs designed for impact across sectors in Africa.',
#         'page_keywords': 'Fellowships, Decision Intelligence Design, Innovation, Public Sector, Research, Emerging Leaders, Kenya, Africa',
#     }
#     return render(request, "home/fellowship/fellowship.html", context)


def academy(request):
    # Get featured programs for the current year with optimized query
    featured_programs = Program.objects.filter(
        is_active=True, 
        is_featured=True, 
        year=2025
    ).select_related().order_by('order')
    
    # Get partners and clients for the academy page
    partners = Partner.objects.filter(is_active=True, is_featured=True).select_related().order_by('order')
    clients = Client.objects.filter(is_active=True, is_featured=True).select_related().order_by('order')
    
    # SEO metadata
    context = {
        'featured_programs': featured_programs,
        'partners': partners,
        'clients': clients,
        'page_title': 'Decision Intelligence Design Academy',
        'page_description': 'Develop critical skills in decision intelligence design through our comprehensive academy programs for professionals, executives, and organizations.',
        'page_keywords': 'Academy, Decision Intelligence Design, Training, Professional Development, Executive Education, Africa, Kenya',
    }
    return render(request, "home/fellowship/academy.html", context)


def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug, is_active=True)
    
    # SEO metadata
    context = {
        'project': project,
        'page_title': project.title,
        'page_description': project.challenge or f'{project.title} - A decision intelligence design project by IDI Africa.',
        'page_keywords': f'{project.tags+", " if project.tags else ""}Decision Intelligence Design, {project.title}, Innovation, Africa, Kenya',
        'page_image': project.thumbnail,
        'og_type': 'article',
    }
    return render(request, 'home/projects/project_detail.html', context)


def program_detail(request, slug):
    program = get_object_or_404(Program, slug=slug, is_active=True)
    
    # SEO metadata
    context = {
        'program': program,
        'page_title': program.title,
        'page_description': program.meta_description if program.meta_description else program.short_description,
        'page_keywords': program.meta_keywords if program.meta_keywords else f'{program.title}, Decision Intelligence Design, Academy, Africa, Kenya',
        'page_image': program.image,
    }
    return render(request, 'home/programs/program_detail.html', context)

# New view for Projects list page (Our Work)
def projects_list(request):
    projects = Project.objects.filter(is_active=True).select_related().order_by('-created_at')
    
    # SEO metadata
    context = {
        'projects': projects,
        'page_title': 'Our Work',
        'page_description': 'Explore our portfolio of decision intelligence design projects across various sectors in Africa.',
        'page_keywords': 'Projects, Decision Intelligence Design, Innovation, Case Studies, Portfolio, Africa, Kenya',
    }
    return render(request, 'home/projects/projects_list.html', context)


# New view for Team page
def team_list(request):
    team_members = TeamMember.objects.select_related().all()
    
    # SEO metadata
    context = {
        'team_members': team_members,
        'page_title': 'Our Team',
        'page_description': 'Meet the passionate innovators, designers, and researchers behind IDI Africa who are driving decision intelligence design across the continent.',
        'page_keywords': 'Team, Decision Intelligence Design, Experts, Leadership, Innovators, Africa, Kenya',
    }
    return render(request, 'home/team/team_list.html', context)
    

class TeamMemberDetailView(DetailView):
    model = TeamMember
    template_name = 'home/team/team_member_detail.html'
    context_object_name = 'member'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = self.get_object()
        
        # Always set single_member to True
        context['single_member'] = True
        
        # SEO metadata
        context['page_title'] = member.name
        context['page_description'] = f'{member.name} - {member.position} at IDI Africa. Learn more about their work in decision intelligence design.'
        context['page_keywords'] = f'Team Member, {member.name}, {member.position}, Decision Intelligence Design, Innovation, Africa, Kenya'
        context['page_image'] = member.image
        
        return context
    



def llms_txt(request):
    """LLM-readable site summary (GEO). Served as text/plain at /llms.txt.

    Includes the live case studies so answer engines can discover and cite individual
    project pages, not just the section landing pages.
    """
    projects = Project.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'seo/llms.txt',
                  {'base': request.build_absolute_uri('/').rstrip('/'),
                   'projects': projects},
                  content_type='text/plain; charset=utf-8')


def custom_page_not_found(request, exception):
    """
    Custom 404 page handler
    """
    context = {
        'page_title': '404 - Page Not Found',
        'page_description': 'The page you were looking for could not be found on IDI Africa.',
        'page_keywords': 'error, 404, page not found, IDI Africa',
    }
    return render(request, '404.html', context, status=404)


def custom_server_error(request):
    """
    Custom 500 page handler
    """
    context = {
        'page_title': '500 - Server Error',
        'page_description': 'We apologize, but something went wrong on our end at IDI Africa.',
        'page_keywords': 'error, 500, server error, IDI Africa',
    }
    return render(request, '404.html', context, status=500)


def custom_permission_denied(request, exception):
    """
    Custom 403 page handler
    """
    context = {
        'page_title': '403 - Permission Denied',
        'page_description': 'You do not have permission to access this page on IDI Africa.',
        'page_keywords': 'error, 403, permission denied, IDI Africa',
    }
    return render(request, '404.html', context, status=403)


def custom_bad_request(request, exception):
    """
    Custom 400 page handler
    """
    context = {
        'page_title': '400 - Bad Request',
        'page_description': 'The request sent to the IDI Africa server was invalid.',
        'page_keywords': 'error, 400, bad request, IDI Africa',
    }
    return render(request, '404.html', context, status=400)