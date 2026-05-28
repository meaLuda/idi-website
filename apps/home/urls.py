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
    # New URL paths
    path('fellowship/did-academy', views.academy, name="did-academy"),
    path('team/<slug:slug>/', views.TeamMemberDetailView.as_view(), name='team_member_detail'),
    path('projects/<slug:slug>/', views.project_detail, name='project_detail'),
    path('programs/<slug:slug>/', views.program_detail, name='program_detail'),
    # New URL paths
    path('projects/', views.projects_list, name='projects_list'),
    path('team/', views.team_list, name='team_list'),
    path('governance-public-service-delivery/', views.governance_public_service_delivery, name='governance_public_service_delivery'),
    path('responsible-sovereign-ai/', views.responsible_sovereign_ai, name='responsible_sovereign_ai'),
    path('community-public-service-delivery/', views.community_public_service_delivery, name='community_public_service_delivery'),
    path('case-studies/reimagining-youth-opportunity-systems/', views.reimagining_youth, name='reimagining_youth'),
    path('food-systems-health-practice/', views.food_systems_health_practice, name='food_systems_health_practice'),
    path('services/', views.services, name='services'),
    path('health/', health_check, name='health_check'),
]