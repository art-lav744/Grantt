from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from tournaments.models import Evaluation, JuryRegistrationStatus, Round, Submission, Team, Tournament, User, UserRole


def make_user(email, nickname, role, password='Password123!', is_verified=True):
    return User.objects.create_user(
        email=email,
        password=password,
        nickname=nickname,
        role=role,
        is_verified=is_verified,
    )


def make_tournament(**kwargs):
    now = timezone.now()
    defaults = dict(
        title='Hackathon 2026',
        description='Desc',
        reg_start=now - timedelta(days=10),
        reg_end=now - timedelta(days=7),
        start_time=now - timedelta(days=6),
        end_time=now - timedelta(days=1),
    )
    defaults.update(kwargs)
    return Tournament.objects.create(**defaults)


def make_round_with_criteria(**kwargs):
    round_obj = Round.objects.create(**kwargs)
    round_obj.set_scoring_criteria([
        {'name': 'Technical', 'max_score': 100},
        {'name': 'Functionality', 'max_score': 100},
    ])
    return round_obj


def make_evaluation(submission, jury, **scores):
    # Since we now have a OneToOneField, each submission can only have one evaluation
    # Delete any existing evaluation first
    Evaluation.objects.filter(submission=submission).delete()
    evaluation = Evaluation.objects.create(submission=submission, jury=jury)
    for score_entry in evaluation.ensure_score_entries():
        if score_entry.criterion.name in scores:
            score_entry.score = scores[score_entry.criterion.name]
            score_entry.save(update_fields=['score'])
    return evaluation


class TournamentLeaderboardFinalTests(TestCase):
    def test_leaderboard_uses_average_of_round_scores(self):
        tournament = make_tournament()
        round1 = make_round_with_criteria(
            tournament=tournament,
            title='R1',
            description='r1',
            requirements='req',
            start_time=timezone.now() - timedelta(days=5),
            end_time=timezone.now() - timedelta(days=4),
        )
        round2 = make_round_with_criteria(
            tournament=tournament,
            title='R2',
            description='r2',
            requirements='req',
            start_time=timezone.now() - timedelta(days=3),
            end_time=timezone.now() - timedelta(days=2),
        )

        team_a = Team.objects.create(name='A Team', tournament=tournament)
        team_b = Team.objects.create(name='B Team', tournament=tournament)
        jury = make_user('jury@test.com', 'jury', UserRole.JURY)
        jury.jury_tournaments.add(tournament)

        sub_a1 = Submission.objects.create(team=team_a, round=round1, github_link='https://g/a1', video_link='https://v/a1', description='a1')
        sub_a2 = Submission.objects.create(team=team_a, round=round2, github_link='https://g/a2', video_link='https://v/a2', description='a2')
        sub_b1 = Submission.objects.create(team=team_b, round=round1, github_link='https://g/b1', video_link='https://v/b1', description='b1')
        sub_b2 = Submission.objects.create(team=team_b, round=round2, github_link='https://g/b2', video_link='https://v/b2', description='b2')

        make_evaluation(sub_a1, jury, Technical=90, Functionality=90)
        make_evaluation(sub_a2, jury, Technical=80, Functionality=80)
        make_evaluation(sub_b1, jury, Technical=100, Functionality=100)
        make_evaluation(sub_b2, jury, Technical=60, Functionality=60)

        response = APIClient().get(f'/api/tournaments/{tournament.id}/leaderboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_final'])
        self.assertEqual(response.data['leaderboard'][0]['team_name'], 'A Team')
        self.assertEqual(response.data['leaderboard'][0]['average_score'], 85.0)
        self.assertEqual(response.data['leaderboard'][1]['average_score'], 80.0)

    def test_leaderboard_sorts_by_average_and_tie_break_fields(self):
        tournament = make_tournament(title='Tie Break Cup')
        round_obj = make_round_with_criteria(
            tournament=tournament,
            title='R1',
            description='desc',
            requirements='req',
            start_time=timezone.now() - timedelta(days=2),
            end_time=timezone.now() - timedelta(days=1),
        )

        jury = make_user('tie-jury@test.com', 'tie_jury', UserRole.JURY)
        jury.jury_tournaments.add(tournament)

        team_alpha = Team.objects.create(name='Alpha', tournament=tournament)
        team_beta = Team.objects.create(name='Beta', tournament=tournament)
        team_gamma = Team.objects.create(name='Gamma', tournament=tournament)

        sub_alpha = Submission.objects.create(team=team_alpha, round=round_obj, github_link='https://g/alpha', video_link='https://v/alpha', description='alpha')
        sub_beta = Submission.objects.create(team=team_beta, round=round_obj, github_link='https://g/beta', video_link='https://v/beta', description='beta')
        sub_gamma = Submission.objects.create(team=team_gamma, round=round_obj, github_link='https://g/gamma', video_link='https://v/gamma', description='gamma')

        make_evaluation(sub_alpha, jury, Technical=70, Functionality=90)
        make_evaluation(sub_beta, jury, Technical=80, Functionality=80)
        make_evaluation(sub_gamma, jury, Technical=60, Functionality=70)

        response = APIClient().get(f'/api/tournaments/{tournament.id}/leaderboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        rows = response.data['leaderboard']
        self.assertEqual([row['team_name'] for row in rows], ['Beta', 'Alpha', 'Gamma'])
        self.assertEqual([row['rank'] for row in rows], [1, 2, 3])
        self.assertEqual(rows[0]['average_score'], 80.0)
        self.assertEqual(rows[1]['average_score'], 80.0)
        self.assertGreater(rows[0]['primary_criterion_avg'], rows[1]['primary_criterion_avg'])


class JuryRegistrationApprovalTests(APITestCase):
    def setUp(self):
        self.tournament = make_tournament(
            end_time=timezone.now() + timedelta(days=2),
            title='Approval Tournament',
        )
        self.admin = make_user('admin@test.com', 'admin', UserRole.ADMIN)
        self.jury = make_user('jury_member@test.com', 'jury_member', UserRole.JURY)

    def test_jury_registration_requires_admin_approval(self):
        self.client.force_authenticate(user=self.jury)
        create_resp = self.client.post('/api/jury/registrations/', {'tournament_id': self.tournament.id}, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_resp.data['status'], JuryRegistrationStatus.PENDING)
        self.assertFalse(self.jury.jury_tournaments.filter(id=self.tournament.id).exists())

        registration_id = create_resp.data['id']

        self.client.force_authenticate(user=self.admin)
        approve_resp = self.client.patch(
            f'/api/jury/registrations/{registration_id}/review/',
            {'status': JuryRegistrationStatus.APPROVED},
            format='json',
        )
        self.assertEqual(approve_resp.status_code, status.HTTP_200_OK)

        self.jury.refresh_from_db()
        self.assertTrue(self.jury.jury_tournaments.filter(id=self.tournament.id).exists())

    def test_distribute_requires_round_to_be_ended(self):
        organizer = make_user('org@test.com', 'org', UserRole.ORGANIZER)
        self.client.force_authenticate(user=organizer)

        active_round = make_round_with_criteria(
            tournament=self.tournament,
            title='Active',
            description='desc',
            requirements='req',
            start_time=timezone.now() - timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=1),
            status='active',
        )
        team = Team.objects.create(name='T1', tournament=self.tournament)
        Submission.objects.create(
            team=team,
            round=active_round,
            github_link='https://g/t1',
            video_link='https://v/t1',
            description='desc',
        )
        self.jury.jury_tournaments.add(self.tournament)

        response = self.client.post(f'/api/rounds/{active_round.id}/distribute/', {'k': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Evaluation.objects.count(), 0)
