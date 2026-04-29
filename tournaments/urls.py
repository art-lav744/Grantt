from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('verify/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('profile/', views.profile_view, name='profile'),
    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('tournament-dashboard/', views.tournament_dashboard, name='tournament_dashboard'),

    path('create-staff/', views.create_staff, name='create_staff'),
    path('tournament/<int:tournament_id>/create-team/', views.create_team, name='create_team'),
    path('tournaments/', views.tournament_list, name='tournament_list'),
    path('tournament/<int:tournament_id>/register/', views.register_for_tournament, name='register_tournament'),
    path('tournament/<int:tournament_id>/apply-jury/', views.apply_as_jury, name='apply_jury'),
    path('tournament/<int:tournament_id>/leaderboard/', views.tournament_leaderboard, name='tournament_leaderboard'),
    path('tournament/<int:tournament_id>/', views.tournament_detail, name='tournament_detail'),

    path('teams/<int:pk>/', views.team_detail, name='team_detail'),
    path('my-team/', views.team_dashboard, name='team_dashboard'),
    path('teams/<int:team_id>/submit/', views.submission_create, name='team_dashboard'),
    
    path('teams/<int:team_id>/add-member/', views.add_team_member, name='add_member'),
    path('tournament/create/', views.tournament_create, name='tournament_create'),
    path('tournament/<int:pk>/edit/', views.tournament_edit, name='tournament_edit'),
    path('tournament/<int:tournament_id>/files/upload/', views.tournament_file_upload, name='tournament_file_upload'),
    path('tournament-files/<int:file_id>/open/', views.tournament_file_open, name='tournament_file_open'),
    path('tournament-files/<int:file_id>/download/', views.tournament_file_download, name='tournament_file_download'),
    path('tournament/<int:tournament_id>/round/create/', views.round_create, name='round_create'),
    path('rounds/<int:round_id>/edit/', views.round_edit, name='round_edit'),
    path('admin-panel/manage-access/', views.manage_access_and_jury, name='manage_access'),
    # Подача роботи (для капітана)
    path('team/<int:team_id>/submit/', views.submission_create, name='submission_create'),
    
    path('evaluation/<int:eval_id>/', views.evaluation_detail, name='evaluation_detail'),
]
