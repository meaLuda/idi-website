from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, DetailView
from .models import Project, TeamMember, Testimonial

# Create your views here.
def home(request):
    team_members = TeamMember.objects.all()[:6]  # Limit to 6 team members for landing page
    projects = Project.objects.filter(is_active=True)[:6]  # Limit projects on home page
    testimonials = Testimonial.objects.filter(is_active=True)
    context = {
        'team_members': team_members,
        'projects': projects,
        'testimonials': testimonials
    }
    return render(request, "home/index.html", context)


def fellowships(request):
    return render(request,"home/fellowship/fellowship.html")


def academy(request):
    return render(request,"home/fellowship/academy.html")


def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug, is_active=True)
    return render(request, 'home/projects/project_detail.html', {'project': project})


# New view for Projects list page (Our Work)
def projects_list(request):
    projects = Project.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'home/projects/projects_list.html', {'projects': projects})


# New view for Team page
def team_list(request):
    team_members = TeamMember.objects.all()
    return render(request, 'home/team/team_list.html', {'team_members': team_members})
    

class TeamMemberDetailView(DetailView):
    model = TeamMember
    template_name = 'home/team_member_detail.html'
    context_object_name = 'member'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['single_member'] = True
        return context