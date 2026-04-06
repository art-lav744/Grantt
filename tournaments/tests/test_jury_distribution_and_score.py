from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from tournaments.models import Evaluation, Round, Submission, Team, Tournament, User, UserRole


def make_tournament(**kwargs):
    """
    ЧАС ТОМУ МОЖЕ БУТИ НЕ ПРАВИЛЬНИЙ ТЕСТ ПРОВАЛИТЬСЯ
    створює турнір з валідними тайм-рамками.
    """
    now = timezone.now()
    defaults = dict(
        title='Hackathon 2025',
        description='Опис турніру',
        reg_start=now - timedelta(days=10),
        reg_end=now - timedelta(days=5),
        start_time=now - timedelta(days=4),
        end_time=now + timedelta(days=10),
    )
    defaults.update(kwargs)
    return Tournament.objects.create(**defaults)


def make_round(tournament, **kwargs):
    """
    ЧАС ТОМУ МОЖЕ БУТИ НЕ ПРАВИЛЬНИЙ ТЕСТ ПРОВАЛИТЬСЯ
    створює раунд з валідним start/end.
    """
    now = timezone.now()
    defaults = dict(
        tournament=tournament,
        title='Раунд 1',
        description='Опис раунду',
        requirements='Вимоги до раунду',
        start_time=now - timedelta(hours=6),
        end_time=now + timedelta(hours=6),
    )
    defaults.update(kwargs)
    return Round.objects.create(**defaults)


def make_user(email, nickname, role, password='Password123!', is_verified=True):
    return User.objects.create_user(
        email=email,
        password=password,
        nickname=nickname,
        role=role,
        is_verified=is_verified,
    )


class SubmissionFinalScoreTest(TestCase):
    def test_calculate_final_score_uses_average_and_total_formula(self):
        tournament = make_tournament()
        team = Team.objects.create(name='Team A', tournament=tournament)
        round_obj = make_round(tournament)
        submission = Submission.objects.create(
            team=team,
            round=round_obj,
            github_link='https://github.com/user/repo1',
            video_link='https://youtube.com/demo1',
            description='Some description',
        )

        jury1 = make_user('jury1@test.com', 'jury1', UserRole.JURY)
        jury2 = make_user('jury2@test.com', 'jury2', UserRole.JURY)

        Evaluation.objects.create(
            submission=submission,
            jury=jury1,
            tech_score=10,
            func_score=50,
        )
        Evaluation.objects.create(
            submission=submission,
            jury=jury2,
            tech_score=30,
            func_score=70,
        )

        result = submission.calculate_final_score()

        self.assertAlmostEqual(result['tech_avg'], 20)
        self.assertAlmostEqual(result['func_avg'], 60)
        self.assertAlmostEqual(result['total'], 40)


class JuryDistributionAPITests(APITestCase):
    """
    ЧАС ТОМУ МОЖЕ БУТИ НЕ ПРАВИЛЬНИЙ ТЕСТ ПРОВАЛИТЬСЯ
    """
    def setUp(self):
        self.tournament = make_tournament()
        self.round_started = make_round(
            self.tournament,
            title='Started Round',
            start_time=timezone.now() - timedelta(minutes=10),
            end_time=timezone.now() + timedelta(hours=1),
        )

        self.organizer = make_user('org@test.com', 'organizer', UserRole.ORGANIZER)
        self.client.force_authenticate(user=self.organizer)

        self.juries = []
        for i in range(3):
            jury = make_user(f'jury{i+1}@test.com', f'jury{i+1}', UserRole.JURY)
            jury.jury_tournaments.add(self.tournament)
            self.juries.append(jury)

        self.team1 = Team.objects.create(name='Team 1', tournament=self.tournament)
        self.team2 = Team.objects.create(name='Team 2', tournament=self.tournament)

        self.sub1 = Submission.objects.create(
            team=self.team1,
            round=self.round_started,
            github_link='https://github.com/user/repo1',
            video_link='https://youtube.com/demo1',
            description='Sub 1',
        )
        self.sub2 = Submission.objects.create(
            team=self.team2,
            round=self.round_started,
            github_link='https://github.com/user/repo2',
            video_link='https://youtube.com/demo2',
            description='Sub 2',
        )

    def test_distribute_endpoint_creates_evaluations_for_each_submission(self):
        url = f'/api/rounds/{self.round_started.id}/distribute/'
        response = self.client.post(url, {'k': 2}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Evaluation.objects.count(), 2 * 2)  # 2 submissions * k_actual(2)

        self.assertEqual(Evaluation.objects.filter(submission=self.sub1).count(), 2)
        self.assertEqual(Evaluation.objects.filter(submission=self.sub2).count(), 2)

    def test_auto_distribution_on_submission_create_if_round_started(self):
        """
        ЧАС ТОМУ МОЖЕ БУТИ НЕ ПРАВИЛЬНИЙ ТЕСТ ПРОВАЛИТЬСЯ
        створення Evaluation для цього раунду.
        """
        Evaluation.objects.all().delete()

        team3 = Team.objects.create(name='Team 3', tournament=self.tournament)
        url = '/api/submissions/'
        payload = {
            'team': team3.id,
            'round': self.round_started.id,
            'github_link': 'https://github.com/user/repo3',
            'video_link': 'https://youtube.com/demo3',
            'description': 'Sub 3',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Evaluation.objects.count(), 3 * 3)

