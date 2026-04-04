
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
        self.organizer = User.objects.create_user(
            email='organizer@gmail.com',
            password='Test1234!',
            nickname='organizer',
            role=UserRole.ORGANIZER,
            is_verified=True,
        )

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


    def test_organizer_can_create_tournament(self):
        self.client.force_login(self.organizer)
        now = timezone.now().replace(second=0, microsecond=0)
        response = self.client.post(reverse('tournament_create'), {
            'title': 'Organizer tournament',
            'description': 'Desc',
            'reg_start': now.strftime('%Y-%m-%dT%H:%M'),
            'reg_end': (now + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'start_time': (now + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
            'end_time': (now + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M'),
            'max_teams': 8,
        })
        self.assertRedirects(response, reverse('dashboard'))
        tournament = Tournament.objects.get(title='Organizer tournament')
        self.assertEqual(tournament.creator, self.organizer)


    def test_organizer_can_edit_own_tournament(self):
        tournament = Tournament.objects.create(
            title='Own tournament',
            description='Desc',
            creator=self.organizer,
            reg_start=timezone.now(),
            reg_end=timezone.now() + timedelta(days=1),
            start_time=timezone.now() + timedelta(days=2),
            end_time=timezone.now() + timedelta(days=3),
            max_teams=8,
        )
        self.client.force_login(self.organizer)
        now = timezone.now().replace(second=0, microsecond=0)
        response = self.client.post(reverse('tournament_edit', args=[tournament.id]), {
            'title': 'Updated by organizer',
            'description': 'New desc',
            'reg_start': now.strftime('%Y-%m-%dT%H:%M'),
            'reg_end': (now + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'start_time': (now + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
            'end_time': (now + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M'),
            'max_teams': 10,
            'min_team_members': 2,
            'max_team_members': 5,
            'status': tournament.status,
        })
        self.assertRedirects(response, reverse('dashboard'))
        tournament.refresh_from_db()
        self.assertEqual(tournament.title, 'Updated by organizer')

    def test_organizer_can_edit_other_users_tournament(self):
        other_tournament = Tournament.objects.create(
            title='Admin tournament',
            description='Desc',
            creator=self.admin,
            reg_start=timezone.now(),
            reg_end=timezone.now() + timedelta(days=1),
            start_time=timezone.now() + timedelta(days=2),
            end_time=timezone.now() + timedelta(days=3),
            max_teams=8,
        )
        self.client.force_login(self.organizer)
        response = self.client.post(reverse('tournament_edit', args=[other_tournament.id]), {
            'title': 'Updated by organizer',
            'description': 'Updated description',
            'reg_start': other_tournament.reg_start.strftime('%Y-%m-%dT%H:%M'),
            'reg_end': other_tournament.reg_end.strftime('%Y-%m-%dT%H:%M'),
            'start_time': other_tournament.start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_time': other_tournament.end_time.strftime('%Y-%m-%dT%H:%M'),
            'max_teams': 12,
        })
        self.assertRedirects(response, reverse('dashboard'))
        other_tournament.refresh_from_db()
        self.assertEqual(other_tournament.title, 'Updated by organizer')
        self.assertEqual(other_tournament.max_teams, 12)
    def test_organizer_can_create_round_for_other_users_tournament(self):
        other_tournament = Tournament.objects.create(
            title='Admin tournament',
            description='Desc',
            creator=self.admin,
            reg_start=timezone.now(),
            reg_end=timezone.now() + timedelta(days=1),
            start_time=timezone.now() + timedelta(days=2),
            end_time=timezone.now() + timedelta(days=3),
            max_teams=8,
        )
        self.client.force_login(self.organizer)
        now = timezone.now().replace(second=0, microsecond=0)
        response = self.client.post(reverse('round_create', args=[other_tournament.id]), {
            'title': 'Round 1',
            'description': 'Round description',
            'requirements': 'Requirements for round 1',
            'start_time': now.strftime('%Y-%m-%dT%H:%M'),
            'end_time': (now + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
        })
        self.assertRedirects(response, reverse('tournament_detail', args=[other_tournament.id]))
        self.assertTrue(other_tournament.rounds.filter(title='Round 1').exists())

