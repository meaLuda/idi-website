from django.urls import path
from django.http import JsonResponse
from . import views

app_name = 'home'

def health_check(request):
    """Simple health check endpoint for Docker health checks"""
    return JsonResponse({'status': 'healthy'})

urlpatterns = [
    path('', views.home, name="lander"),
    path('articles/', views.articles, name="articles"),
    # path('fellowship/did-fellowships',view=views.fellowships,name="did-fellowships"),
    path('fellowship/did-academy', views.academy, name="did-academy"),
    path('team/<slug:slug>/', views.TeamMemberDetailView.as_view(), name='team_member_detail'),
    path('projects/<slug:slug>/', views.project_detail, name='project_detail'),
    path('programs/<slug:slug>/', views.program_detail, name='program_detail'),
    # New URL paths
    path('projects/', views.projects_list, name='projects_list'),
    path('team/', views.team_list, name='team_list'),
    path('health/', health_check, name='health_check'),
]