from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from tournaments.models import Round, RoundStatus, Tournament, TournamentStatus, User, UserRole


class RoundUiTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com', password='pass12345', nickname='admin',
            full_name='Admin User', role=UserRole.ADMIN, is_verified=True,
        )
        self.participant = User.objects.create_user(
            email='participant@example.com', password='pass12345', nickname='participant',
            full_name='Participant User', role=UserRole.PARTICIPANT, is_verified=True,
        )
        now = timezone.now()
        self.tournament = Tournament.objects.create(
            title='UI Tournament', description='Test tournament', status=TournamentStatus.REGISTRATION,
            creator=self.admin, reg_start=now - timezone.timedelta(days=1),
            reg_end=now + timezone.timedelta(days=1), start_time=now,
            end_time=now + timezone.timedelta(days=10), max_rounds=5,
            min_team_members=1, max_team_members=5,
        )
        self.round = Round.objects.create(
            tournament=self.tournament, title='Round 1', description='Old description',
            requirements='Old requirements', start_time=now,
            end_time=now + timezone.timedelta(days=2), status=RoundStatus.ACTIVE,
        )
        self.future_round = Round.objects.create(
            tournament=self.tournament, title='Future Round', description='Future description',
            requirements='Future requirements', start_time=now + timezone.timedelta(days=2),
            end_time=now + timezone.timedelta(days=4), status=RoundStatus.DRAFT,
        )

    def test_admin_sees_round_edit_link_on_tournament_detail(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('tournament_detail', args=[self.tournament.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('round_edit', args=[self.round.id]))
        self.assertContains(response, 'Редагувати')

    def test_participant_does_not_see_round_edit_link(self):
        self.client.force_login(self.participant)
        response = self.client.get(reverse('tournament_detail', args=[self.tournament.id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse('round_edit', args=[self.round.id]))

    def test_admin_can_edit_round_from_ui(self):
        self.client.force_login(self.admin)
        start = timezone.localtime(self.round.start_time).strftime('%Y-%m-%dT%H:%M')
        end = timezone.localtime(self.round.end_time + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        response = self.client.post(reverse('round_edit', args=[self.round.id]), {
            'title': 'Updated Round', 'description': 'Updated description',
            'requirements': 'Updated requirements', 'start_time': start,
            'end_time': end, 'status': RoundStatus.CLOSED,
            'criteria_definition': 'Technical | 100',
        })
        self.assertRedirects(response, reverse('tournament_detail', args=[self.tournament.id]))
        self.round.refresh_from_db()
        self.assertEqual(self.round.title, 'Updated Round')
        self.assertEqual(self.round.status, RoundStatus.CLOSED)
        self.assertEqual(self.round.evaluation_criteria, 'Technical | 100')

    def test_participant_cannot_open_round_edit_page(self):
        self.client.force_login(self.participant)
        response = self.client.get(reverse('round_edit', args=[self.round.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('home'))

    def test_api_rounds_visible_after_start_for_regular_users(self):
        client = APIClient()
        client.force_authenticate(user=self.participant)

        response = client.get('/api/rounds/', {'tournament_id': self.tournament.id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['title'] for item in response.data], ['Round 1'])

    def test_api_rounds_always_visible_for_admin(self):
        client = APIClient()
        client.force_authenticate(user=self.admin)

        response = client.get('/api/rounds/', {'tournament_id': self.tournament.id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['title'] for item in response.data], ['Round 1', 'Future Round'])
