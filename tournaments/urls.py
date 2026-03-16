from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('tournaments/', views.tournament_list, name='tournament_list'),
    path('tournaments/<int:pk>/', views.tournament_detail, name='tournament_detail'),
    path('teams/<int:pk>/', views.team_detail, name='team_detail'),
    path('teams/<int:team_id>/submit/', views.submission_create, name='submission_create'),
]
