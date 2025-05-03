from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, DetailView
from .models import Project, TeamMember, Testimonial

# Create your views here.
def home(request):
    team_members = TeamMember.objects.all()[:6]  # Limit to 6 team members for landing page
    projects = Project.objects.filter(is_active=True)[:6]  # Limit projects on home page
    testimonials = Testimonial.objects.filter(is_active=True)
    
    # SEO metadata
    context = {
        'team_members': team_members,
        'projects': projects,
        'testimonials': testimonials,
        'page_title': 'Home',
        'page_description': 'IDI Africa pioneers Decision Intelligence Design in Africa, transforming complexity into actionable solutions through our innovative fellowship programs and impactful initiatives.',
        'page_keywords': 'Decision Intelligence, Design Thinking, AI, Innovation, Fellowship, Africa, Kenya',
    }
    return render(request, "home/index.html", context)


def fellowships(request):
    # SEO metadata
    context = {
        'page_title': 'Decision Intelligence Design Fellowships',
        'page_description': 'Transform complexity into actionable solutions through our immersive fellowship programs designed for impact across sectors in Africa.',
        'page_keywords': 'Fellowships, Decision Intelligence Design, Innovation, Public Sector, Research, Emerging Leaders, Kenya, Africa',
    }
    return render(request, "home/fellowship/fellowship.html", context)


def academy(request):
    # SEO metadata
    context = {
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
        'page_description': f'{project.title} - A decision intelligence design project by IDI Africa.',
        'page_keywords': f'Project, Decision Intelligence Design, {project.title}, Innovation, Africa, Kenya',
        'page_image': project.thumbnail,
    }
    return render(request, 'home/projects/project_detail.html', context)


# New view for Projects list page (Our Work)
def projects_list(request):
    projects = Project.objects.filter(is_active=True).order_by('-created_at')
    
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
    team_members = TeamMember.objects.all()
    
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
    template_name = 'home/team_member_detail.html'
    context_object_name = 'member'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = self.get_object()
        
        # SEO metadata
        context['single_member'] = True
        context['page_title'] = member.name
        context['page_description'] = f'{member.name} - {member.position} at IDI Africa. Learn more about their work in decision intelligence design.'
        context['page_keywords'] = f'Team Member, {member.name}, {member.position}, Decision Intelligence Design, Innovation, Africa, Kenya'
        context['page_image'] = member.image
        
        return context
    



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