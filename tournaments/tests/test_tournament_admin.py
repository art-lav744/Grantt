from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from tournaments.models import Tournament, User, UserRole


class TournamentAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@gmail.com',
            password='Test1234!',
            nickname='admin',
            role=UserRole.ADMIN,
            is_verified=True,
            is_staff=True,
        )

    def test_admin_dashboard_opens(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Панель керування турнірами')

    def test_tournament_create_success(self):
        self.client.force_login(self.admin)
        now = timezone.now().replace(second=0, microsecond=0)
        response = self.client.post(reverse('tournament_create'), {
            'title': 'Test tournament',
            'description': 'Desc',
            'reg_start': now.strftime('%Y-%m-%dT%H:%M'),
            'reg_end': (now + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'start_time': (now + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
            'end_time': (now + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M'),
            'max_teams': 8,
        })
        self.assertRedirects(response, reverse('dashboard'))
        tournament = Tournament.objects.get(title='Test tournament')
        self.assertEqual(tournament.creator, self.admin)
        self.assertEqual(tournament.status, 'draft')

    def test_create_staff_marks_admin_verified_and_staff(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('create_staff'), {
            'email': 'jury@gmail.com',
            'role': 'jury',
        })
        self.assertRedirects(response, reverse('dashboard'))
        jury = User.objects.get(email='jury@gmail.com')
        self.assertTrue(jury.is_verified)
        self.assertFalse(jury.is_staff)
