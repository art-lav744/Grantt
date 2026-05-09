from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from tournaments.models import (
    Evaluation,
    EvaluationCriterionScore,
    Round,
    RoundStatus,
    Submission,
    SubmissionStatus,
    Team,
    TeamMember,
    Tournament,
    TournamentStatus,
    User,
    UserRole,
)


def make_user(email, nickname, role=UserRole.PARTICIPANT):
    return User.objects.create_user(
        email=email,
        password='Test1234!',
        nickname=nickname,
        role=role,
        is_verified=True,
    )


def make_tournament(**kwargs):
    now = timezone.now()
    defaults = {
        'title': 'Pass4 tournament',
        'description': 'Desc',
        'status': TournamentStatus.REGISTRATION,
        'reg_start': now - timedelta(days=1),
        'reg_end': now + timedelta(days=1),
        'start_time': now + timedelta(days=2),
        'end_time': now + timedelta(days=3),
        'max_teams': 10,
        'min_team_members': 1,
        'max_team_members': 5,
    }
    defaults.update(kwargs)
    return Tournament.objects.create(**defaults)


class CompletedRoundsAPITests(APITestCase):
    def setUp(self):
        self.admin = make_user('admin_pass4@gmail.com', 'adminpass4', UserRole.ADMIN)
        self.tournament = make_tournament()
        now = timezone.now()
        self.completed_round = Round.objects.create(
            tournament=self.tournament,
            title='Completed round',
            description='Desc',
            requirements='Req',
            start_time=now - timedelta(days=3),
            end_time=now - timedelta(days=2),
            status=RoundStatus.CLOSED,
        )
        self.active_round = Round.objects.create(
            tournament=self.tournament,
            title='Active round',
            description='Desc',
            requirements='Req',
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
            status=RoundStatus.ACTIVE,
        )

    def test_public_rounds_endpoint_shows_only_completed_rounds(self):
        response = self.client.get('/api/rounds/', {'tournament_id': self.tournament.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item['id'] for item in response.data], [self.completed_round.id])

    def test_admin_rounds_endpoint_shows_all_rounds_and_can_edit_existing_round(self):
        self.client.force_authenticate(user=self.admin)

        list_response = self.client.get('/api/rounds/', {'tournament_id': self.tournament.id})
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual({item['id'] for item in list_response.data}, {self.completed_round.id, self.active_round.id})

        patch_response = self.client.patch(
            f'/api/rounds/{self.active_round.id}/',
            {'title': 'Edited active round'},
            format='json',
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.active_round.refresh_from_db()
        self.assertEqual(self.active_round.title, 'Edited active round')


class TournamentTeamsVisibilityAPITests(APITestCase):
    def setUp(self):
        self.organizer = make_user('organizer_pass4@gmail.com', 'organizerpass4', UserRole.ORGANIZER)
        self.tournament = make_tournament(
            creator=self.organizer,
            hide_teams_until_registration_end=True,
            reg_end=timezone.now() + timedelta(days=1),
        )
        self.team = Team.objects.create(
            name='Hidden Team',
            tournament=self.tournament,
            captain_email='captain_pass4@gmail.com',
            captain_name='Captain',
        )
        TeamMember.objects.create(team=self.team, full_name='Captain', email='captain_pass4@gmail.com')

    def test_public_teams_endpoint_hides_teams_until_registration_end(self):
        response = self.client.get(f'/api/tournaments/{self.tournament.id}/teams/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_organizer_can_see_hidden_teams_with_member_count(self):
        self.client.force_authenticate(user=self.organizer)

        response = self.client.get(f'/api/tournaments/{self.tournament.id}/teams/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Hidden Team')
        self.assertEqual(response.data[0]['members_count'], 1)

    def test_public_teams_endpoint_shows_teams_after_registration_end(self):
        self.tournament.reg_end = timezone.now() - timedelta(minutes=1)
        self.tournament.save(update_fields=['reg_end'])

        response = self.client.get(f'/api/tournaments/{self.tournament.id}/teams/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['members_count'], 1)


class JuryEvaluationStatusAPITests(APITestCase):
    def setUp(self):
        self.jury = make_user('jury_pass4@gmail.com', 'jurypass4', UserRole.JURY)
        self.tournament = make_tournament()
        self.round = Round.objects.create(
            tournament=self.tournament,
            title='Round for jury',
            description='Desc',
            requirements='Req',
            start_time=timezone.now() - timedelta(days=2),
            end_time=timezone.now() - timedelta(days=1),
            status=RoundStatus.CLOSED,
        )
        self.round.set_scoring_criteria([{'name': 'Technical', 'max_score': 100}])
        self.team = Team.objects.create(name='Jury Team', tournament=self.tournament)
        self.submission = Submission.objects.create(
            team=self.team,
            round=self.round,
            github_link='https://github.com/example/repo',
            video_link='https://youtube.com/watch?v=demo',
            description='Submission',
        )
        self.evaluation = Evaluation.objects.create(submission=self.submission, jury=self.jury)
        self.client.force_authenticate(user=self.jury)

    def test_my_evaluations_returns_pending_and_evaluated_statuses(self):
        response = self.client.get('/api/users/me/evaluations/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], SubmissionStatus.PENDING)

        score = EvaluationCriterionScore.objects.get(evaluation=self.evaluation)
        score.score = 75
        score.save(update_fields=['score'])

        response = self.client.get('/api/users/me/evaluations/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['status'], SubmissionStatus.EVALUATED)
