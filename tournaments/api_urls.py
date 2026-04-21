from django.urls import path

from . import views

urlpatterns = [
    path('auth/register/', views.RegisterView.as_view(), name='api_register'),
    path('auth/login/', views.LoginView.as_view(), name='api_login'),
    path('users/me/profile-image/', views.UserProfileImageUploadView.as_view(), name='api_profile_image'),
    path('users/me/teams/', views.MyTeamInfoView.as_view(), name='api_my_teams'),
    path('users/me/evaluations/', views.MyEvaluationsView.as_view(), name='api_my_evaluations'),
    path('tournaments/', views.TournamentListCreateView.as_view(), name='api_tournaments'),
    path('tournaments/<int:tournament_id>/status/', views.TournamentStatusUpdateView.as_view(), name='api_tournament_status'),
    path('tournaments/<int:tournament_id>/image/', views.TournamentImageUploadView.as_view(), name='api_tournament_image'),
    path('tournaments/<int:tournament_id>/leaderboard/', views.TournamentLeaderboardView.as_view(), name='api_tournament_leaderboard'),
    path('tournaments/<int:tournament_id>/files/', views.TournamentFileListCreateView.as_view(), name='api_tournament_files'),
    path('teams/', views.TeamCreateView.as_view(), name='api_team_create'),
    path('teams/<int:team_id>/image/', views.TeamImageUploadView.as_view(), name='api_team_image'),
    path('members/<str:email>/tournaments/', views.MemberTournamentsView.as_view(), name='api_member_tournaments'),
    path('rounds/', views.RoundCreateView.as_view(), name='api_round_create'),
    path('rounds/<int:round_id>/distribute/', views.DistributeWorksView.as_view(), name='api_distribute_works'),
    path('submissions/', views.SubmissionCreateView.as_view(), name='api_submission_create'),
    path('admin/teams/<int:team_id>/', views.AdminTeamDetailView.as_view(), name='admin_team_delete'),
    path('admin/members/<int:member_id>/', views.AdminMemberDeleteView.as_view(), name='admin_member_delete'),
    path('rounds/active/', views.ActiveTaskView.as_view(), name='api_active_round'),
]
