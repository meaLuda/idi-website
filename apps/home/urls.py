from django.db import models
from . import views
from django.urls import path

app_name = 'home'

urlpatterns = [
    path('',view=views.home,name="lander"),
    path('fellowship/did-fellowships',view=views.fellowships,name="did-fellowships"),
    path('fellowship/decision-intelligence-design-academy',view=views.academy,name="decision-intelligence-design-academy"),
    path('team/<slug:slug>/', views.TeamMemberDetailView.as_view(), name='team_member_detail'),
    path('projects/<slug:slug>/', views.project_detail, name='project_detail'),
    # New URL paths
    path('projects/', views.projects_list, name='projects_list'),
    path('team/', views.team_list, name='team_list'),
]