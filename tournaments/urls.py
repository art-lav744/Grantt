from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('verify/<uidb64>/<token>/', views.verify_email, name='verify_email'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/', views.tournament_dashboard, name='tournament_dashboard'),

    path('create-staff/', views.create_staff, name='create_staff'),
    path('tournament/<int:tournament_id>/create-team/', views.create_team, name='create_team'),
    path('tournaments/', views.tournament_list, name='tournament_list'),
    path('tournament/<int:tournament_id>/register/', views.register_for_tournament, name='register_tournament'),
    path('tournament/<int:tournament_id>/', views.tournament_detail, name='tournament_detail'),

    path('teams/<int:pk>/', views.team_detail, name='team_detail'),
    path('my-team/', views.team_dashboard, name='team_dashboard'),
    path('teams/<int:team_id>/submit/', views.submission_create, name='submission_create'),
    
    path('teams/<int:team_id>/add-member/', views.add_team_member, name='add_member'),
    path('tournament/create/', views.tournament_create, name='tournament_create'),
    path('tournament/<int:pk>/edit/', views.tournament_edit, name='tournament_edit'),
]
