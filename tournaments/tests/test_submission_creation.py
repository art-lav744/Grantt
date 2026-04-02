from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from tournaments.models import User, Team, Round, Submission, Tournament
from tournaments.forms import SubmissionForm
from tournaments.serializers import SubmissionCreateSerializer


def make_tournament(**kwargs):
    # хелпер для створення турніру з дефолтними значеннями часу
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
    # хелпер для створення раунду з дефолтними значеннями
    now = timezone.now()
    defaults = dict(
        tournament=tournament,
        title='Раунд 1',
        description='Опис раунду',
        requirements='Вимоги до раунду',
        start_time=now - timedelta(hours=2),
        end_time=now + timedelta(hours=2),
    )
    defaults.update(kwargs)
    return Round.objects.create(**defaults)


class SubmissionFormTest(TestCase):

    def setUp(self):
        # створюємо турнір, команду та відкритий раунд для тестів форми
        self.tournament = make_tournament()
        self.team = Team.objects.create(name='Team A', tournament=self.tournament)
        self.open_round = make_round(self.tournament)

    def test_form_valid_with_all_required_fields(self):
        # форма з усіма обов'язковими полями має бути валідною
        form = SubmissionForm(data={
            'round': self.open_round.id,
            'github_link': 'https://github.com/user/repo',
            'video_link': 'https://youtube.com/demo',
            'description': 'Короткий опис проєкту.',
        }, team=self.team)
        self.assertTrue(form.is_valid())

    def test_github_link_is_required(self):
        # форма без github_link має бути невалідною — це обов'язкове поле
        form = SubmissionForm(data={
            'round': self.open_round.id,
            'github_link': '',
            'video_link': 'https://youtube.com/demo',
            'description': 'Опис.',
        }, team=self.team)
        self.assertFalse(form.is_valid())
        self.assertIn('github_link', form.errors)

    def test_video_link_is_required(self):
        # ОЧІКУЄТЬСЯ ПОМИЛКА — video_link має бути обов'язковим,
        # але зараз у моделі стоїть blank=True, null=True
        form = SubmissionForm(data={
            'round': self.open_round.id,
            'github_link': 'https://github.com/user/repo',
            'video_link': '',
            'description': 'Опис.',
        }, team=self.team)
        self.assertFalse(form.is_valid(), "video_link має бути обов'язковим полем")

    def test_description_is_required(self):
        # ОЧІКУЄТЬСЯ ПОМИЛКА — description має бути обов'язковим,
        # але зараз у моделі стоїть blank=True, null=True
        form = SubmissionForm(data={
            'round': self.open_round.id,
            'github_link': 'https://github.com/user/repo',
            'video_link': 'https://youtube.com/demo',
            'description': '',
        }, team=self.team)
        self.assertFalse(form.is_valid(), "description має бути обов'язковим полем")

    def test_live_demo_field_is_optional(self):
        # ОЧІКУЄТЬСЯ ПОМИЛКА — поле live_demo взагалі відсутнє в моделі
        self.assertTrue(
            hasattr(Submission, 'live_demo'),
            "У моделі Submission відсутнє опціональне поле 'live_demo'",
        )


class SubmissionCreateViewTest(TestCase):

    def setUp(self):
        # створюємо верифікованого користувача, команду та відкритий раунд
        self.user = User.objects.create_user(
            email='captain@gmail.com',
            password='Test1234!',
            nickname='captain',
            is_verified=True,
        )
        self.client.force_login(self.user)
        self.tournament = make_tournament()
        self.team = Team.objects.create(
            name='Team A',
            tournament=self.tournament,
            captain=self.user,
        )
        self.open_round = make_round(self.tournament)
        self.url = reverse('submission_create', kwargs={'team_id': self.team.id})

    def test_submit_creates_submission_and_redirects(self):
        # валідний POST має створити сабміт і перенаправити на сторінку команди
        response = self.client.post(self.url, {
            'round': self.open_round.id,
            'github_link': 'https://github.com/user/repo',
            'video_link': 'https://youtube.com/demo',
            'description': 'Опис проєкту.',
        })
        self.assertRedirects(response, reverse('team_detail', kwargs={'pk': self.team.id}))
        self.assertEqual(Submission.objects.count(), 1)

    def test_resubmit_updates_existing_submission(self):
        # повторний сабміт до дедлайну має оновлювати існуючий запис
        Submission.objects.create(
            team=self.team,
            round=self.open_round,
            github_link='https://github.com/user/old',
        )
        self.client.post(self.url, {
            'round': self.open_round.id,
            'github_link': 'https://github.com/user/updated',
            'video_link': 'https://youtube.com/demo',
            'description': 'Оновлений опис.',
        })
        sub = Submission.objects.get(team=self.team, round=self.open_round)
        self.assertEqual(sub.github_link, 'https://github.com/user/updated')

    def test_cannot_edit_after_deadline(self):
        # ОЧІКУЄТЬСЯ ПОМИЛКА — у view відсутня перевірка дедлайну
        # (перевірка є лише в серіалайзері, але не у form view)
        closed_round = make_round(
            self.tournament,
            title='Закритий раунд',
            start_time=timezone.now() - timedelta(hours=4),
            end_time=timezone.now() - timedelta(hours=1),
        )
        Submission.objects.create(
            team=self.team,
            round=closed_round,
            github_link='https://github.com/user/original',
        )
        self.client.post(self.url, {
            'round': closed_round.id,
            'github_link': 'https://github.com/user/sneaky-update',
            'video_link': '',
            'description': '',
        })
        sub = Submission.objects.get(team=self.team, round=closed_round)
        self.assertEqual(
            sub.github_link,
            'https://github.com/user/original',
            "Сабміт був змінений після дедлайну — view має перевіряти round.end_time",
        )

    def test_unauthenticated_user_cannot_submit(self):
        # незалогінений користувач не повинен мати доступ до сторінки сабміту
        self.client.logout()
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)


class SubmissionSerializerTest(TestCase):

    def setUp(self):
        # створюємо турнір і команду для тестів серіалайзера
        self.tournament = make_tournament()
        self.team = Team.objects.create(name='Team B', tournament=self.tournament)

    def test_serializer_rejects_submission_after_deadline(self):
        # серіалайзер має відхиляти сабміт після закінчення раунду
        closed_round = make_round(
            self.tournament,
            title='Закритий раунд',
            start_time=timezone.now() - timedelta(hours=4),
            end_time=timezone.now() - timedelta(seconds=1),
        )
        serializer = SubmissionCreateSerializer(data={
            'team': self.team.id,
            'round': closed_round.id,
            'github_link': 'https://github.com/user/repo',
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_serializer_accepts_submission_within_deadline(self):
        # серіалайзер має приймати сабміт поки раунд ще відкритий
        open_round = make_round(self.tournament, title='Відкритий раунд')
        serializer = SubmissionCreateSerializer(data={
            'team': self.team.id,
            'round': open_round.id,
            'github_link': 'https://github.com/user/repo',
        })
        self.assertTrue(serializer.is_valid())