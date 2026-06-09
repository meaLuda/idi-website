from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from django.views.generic import ListView, DetailView
from .models import Project, TeamMember, Testimonial, Program, Partner, Client, HomeStat, ServicePillar

ARTICLE_PAGE_SIZE = 5

PRACTICE_TILES = [
    {"num": "01", "slug": "food-systems-health-practice", "title": "FOOD SYSTEMS PRACTICE"},
    {"num": "02", "slug": "sustainability-practice", "title": "HEALTH"},
    {"num": "03", "slug": "community-public-service-delivery", "title": "environment"},
    {"num": "04", "slug": "responsible-sovereign-ai", "title": "Responsible / Sovereign AI"},
    {"num": "05", "slug": "governance-public-service-delivery", "title": "Governance & Public Service Delivery"},
    {"num": "06", "slug": "venture-building-innovation-ecosystems", "title": "Venture Building & Innovation Ecosystems"},
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


def civic_innovation_fellowship(request):
    """
    View for the Democratic Futures Civic Innovation Fellowship page.
    """
    context = {
        'page_title': 'Democratic Futures Civic Innovation Fellowship 2026',
        'page_description': "Building Kenya's Next Generation of Public Innovators. A fellowship to cultivate professionals who bridge technology, governance, and civic responsibility.",
        'page_keywords': 'Civic Innovation, Fellowship, Kenya, Public Innovators, Digital Governance, Decision Intelligence',
    }
    return render(request, 'home/fellowship/civic_innovation.html', context)


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
    if slug == 'the-mombasa-county-plastics-prize':
        return render(request, 'home/projects/mombasa_plastics.html', context)
    elif slug == 'space-ai':
        return render(request, 'home/projects/space_ai.html', context)
    elif slug == 'be-green':
        return render(request, 'home/projects/be_green.html', context)
        
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
    
    mock_articles = [
        {
            "category": "Policy",
            "title": "The Future of Public Service Delivery",
            "excerpt": "How decision intelligence design is transforming public service delivery across Africa.",
            "tags": ["Governance", "Public Service Delivery"],
            "date": "January 2026",
        },
        {
            "category": "AI",
            "title": "Building Inclusive AI Governance Frameworks",
            "excerpt": "Designing AI architectures that are trusted, context-aware, and built for long-term public value.",
            "tags": ["AI", "Governance", "Design"],
            "date": "December 2025",
        },
        {
            "category": "Toolkit",
            "title": "Sustainability Toolkit: Measurement Frameworks",
            "excerpt": "Practical tools for tracking and measuring sustainability impacts across public initiatives.",
            "tags": ["Sustainability", "Measurement", "Toolkit"],
            "date": "December 2025",
        },
        {
            "category": "Ecosystems",
            "title": "Venture Ecosystem Rapid Assessment",
            "excerpt": "A comprehensive framework for evaluating and developing local venture building ecosystems.",
            "tags": ["Venture", "Ecosystem", "Innovation"],
            "date": "November 2025",
        },
        {
            "category": "Health",
            "title": "The Role of Design in Health Systems",
            "excerpt": "Why service design is critical to building resilient, responsive, and patient-centric healthcare systems.",
            "tags": ["Health", "Design", "Systems"],
            "date": "November 2025",
        },
        {
            "category": "Playbook",
            "title": "Innovation Challenges: Implementation Playbook",
            "excerpt": "A step-by-step guide to designing, launching, and managing public sector innovation challenges.",
            "tags": ["Innovation", "Design", "Implementation"],
            "date": "October 2025",
        }
    ]
    
    # SEO metadata
    context = {
        'projects': projects,
        'mock_articles': mock_articles,
        'page_title': 'Insights',
        'page_description': 'Research, thought leadership, and tools. Bringing context, representation, and deep decision intelligence to structural transitions.',
        'page_keywords': 'Insights, Decision Intelligence Design, Research, Whitepapers, Africa, Innovation',
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


def governance_public_service_delivery(request):
    """
    View for the Governance & Public Service Delivery practice page.
    """
    context = {
        'page_title': 'Governance & Public Service Delivery',
        'page_description': 'Designing systems that govern effectively—and deliver where it matters. IDI Africa works at the intersection of decision intelligence and public service delivery.',
        'page_keywords': 'Governance, Public Service Delivery, Decision Intelligence, System Design, Africa, Innovation',
    }
    return render(request, 'home/governance_public_service_delivery.html', context)


def responsible_sovereign_ai(request):
    """
    View for the Responsible / Sovereign AI practice page.
    """
    context = {
        'page_title': 'Responsible & Sovereign AI',
        'page_description': 'Designing AI systems that are trusted, context-aware, and built for long-term public value. IDI Africa pioneers representational and ethical AI architectures.',
        'page_keywords': 'Sovereign AI, Responsible AI, AI Ethics, Civic Tech, Machine Learning, Africa, Innovation',
    }
    return render(request, 'home/responsible_sovereign_ai.html', context)


def community_public_service_delivery(request):
    """
    View for the Community & Public Service Delivery practice page.
    """
    context = {
        'page_title': 'Community & Public Service Delivery',
        'page_description': 'Designing for relevance. We build frameworks, strategy, and products that respect and reflect community context, knowledge, and sovereignty.',
        'page_keywords': 'Community Service, Public Service Delivery, Participatory Design, Civic Trust, Decision Intelligence, Africa, Innovation',
    }
    return render(request, 'home/community_public_service_delivery.html', context)


def food_systems_health_practice(request):
    """
    View for the Food Systems & Health Practice practice page.
    """
    context = {
        'page_title': 'Food Systems & Health Practice',
        'page_description': 'Designing for relevance. We build frameworks, strategy, and products that respect and reflect community context, knowledge, and sovereignty within food systems.',
        'page_keywords': 'Food Systems, Health Practice, Nutrition, Agricultural Decision Systems, Public Health, Decision Intelligence, Africa, Innovation',
    }
    return render(request, 'home/food_systems_health_practice.html', context)


def reimagining_youth(request):
    """
    View for the Reimagining Youth Opportunity Systems case study page.
    """
    context = {
        'page_title': 'Reimagining Youth Opportunity Systems',
        'page_description': 'A case study on digitizing knowledge economies and civic engagement within government frameworks.',
        'page_keywords': 'Youth Opportunity, Government, Civic Literacy, Decision Intelligence, Case Study',
    }
    return render(request, 'home/projects/reimagining_youth.html', context)


def services(request):
    """
    View for the dedicated Services page.
    """
    service_pillars = ServicePillar.objects.filter(is_active=True)
    
    # SEO metadata
    context = {
        'service_pillars': service_pillars,
        'page_title': 'Services',
        'page_description': 'Decision Intelligence Design for modern structural transitions. Discover our service pillars across Strategy & Design, Insights & Data, and Implementation & Scale.',
        'page_keywords': 'Services, Strategy, Design, Insights, Data, Implementation, Scale, Decision Intelligence, Africa, Innovation',
    }
    return render(request, 'home/services.html', context)


def sustainability_practice(request):
    """
    View for the Health (formerly Sustainability) practice page.
    """
    context = {
        'page_title': 'Health',
        'page_description': 'Designing for health and resilience. We build custom decision intelligence frameworks for healthcare systems across Africa.',
        'page_keywords': 'Health, Decision Intelligence, Healthcare, Africa, Innovation',
    }
    return render(request, 'home/sustainability_practice.html', context)


def venture_building(request):
    """
    View for the Venture Building & Innovation Ecosystems practice page.
    """
    context = {
        'page_title': 'Venture Building & Innovation Ecosystems',
        'page_description': 'Accelerating growth and building robust innovation ecosystems across the African continent.',
        'page_keywords': 'Venture Building, Innovation, Ecosystems, Startups, Scale, Africa',
    }
    return render(request, 'home/venture_building.html', context)


def contact(request):
    """
    View for the dedicated Contact Us page.
    """
    success = False
    if request.method == "POST":
        # Process visual inquiry submission
        success = True
        
    context = {
        'success': success,
        'page_title': 'Contact Us',
        'page_description': 'Get in touch with IDI Africa. Whether you want to partner with us, join our fellowship, or initiate an inquiry, we would love to hear from you.',
        'page_keywords': 'Contact, Inquiry, Partnership, Decision Intelligence, Africa, Kenya, Nairobi',
    }
    return render(request, "home/contact.html", context)