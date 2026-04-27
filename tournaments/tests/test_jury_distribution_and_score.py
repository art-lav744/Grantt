from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from tournaments.models import Evaluation, EvaluationCriterionScore, Round, Submission, Team, Tournament, User, UserRole


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
    round_obj = Round.objects.create(**defaults)
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

        make_evaluation(submission, jury1, Technical=10, Functionality=50)

        result = submission.calculate_final_score()

        self.assertAlmostEqual(result['criteria_avg_map']['Technical'], 10)
        self.assertAlmostEqual(result['criteria_avg_map']['Functionality'], 50)
        self.assertAlmostEqual(result['raw_total'], 60)
        self.assertAlmostEqual(result['total'], 30)


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
        self.round_started.end_time = timezone.now() - timedelta(minutes=1)
        self.round_started.save(update_fields=['end_time'])
        url = f'/api/rounds/{self.round_started.id}/distribute/'
        response = self.client.post(url, {'k': 2}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Evaluation.objects.count(), 2)  # 2 submissions, 1 jury each
        self.assertEqual(EvaluationCriterionScore.objects.count(), 2 * 2)  # 2 submissions * 2 criteria

        self.assertEqual(Evaluation.objects.filter(submission=self.sub1).count(), 1)
        self.assertEqual(Evaluation.objects.filter(submission=self.sub2).count(), 1)

    def test_submission_create_does_not_auto_distribute_before_round_end(self):
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
        self.assertEqual(Evaluation.objects.count(), 0)

