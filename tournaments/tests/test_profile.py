from django.test import TestCase
from django.urls import reverse
from tournaments.models import User, Team, TeamMember, Tournament, Submission, Round
from django.utils import timezone
from datetime import timedelta

class ProfileViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@test.com', nickname='user_nick', password='Password123!', is_verified=True
        )
        self.other_user = User.objects.create_user(
            email='other@test.com', nickname='other_nick', password='Password123!', is_verified=True
        )
        self.tournament = Tournament.objects.create(
            title="T1", reg_start=timezone.now(), reg_end=timezone.now()+timedelta(days=1),
            start_time=timezone.now(), end_time=timezone.now()+timedelta(days=2), creator=self.user
        )
        # Команда, де юзер капітан
        self.team_captain = Team.objects.create(name="Captain Team", tournament=self.tournament, captain=self.user)
        # Команда, де юзер просто учасник
        self.team_member = Team.objects.create(name="Member Team", tournament=self.tournament, captain=self.other_user)
        TeamMember.objects.create(team=self.team_member, user=self.user, full_name="Test User", email=self.user.email)

    def test_profile_context_filtering(self):
        """Перевірка що команди правильно розподіляються за ролями"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('profile'))
        
        self.assertIn(self.team_captain, response.context['captain_teams'])
        self.assertIn(self.team_member, response.context['member_teams'])
        self.assertNotIn(self.team_captain, response.context['member_teams'])

    def test_profile_edit_nickname_collision(self):
        """Не можна змінити нікнейм на той, що вже зайнятий іншим"""
        self.client.force_login(self.user)
        response = self.client.post(reverse('profile'), {
            'nickname': 'other_nick', # вже існує
            'full_name': 'New Name',
            'discord_tag': 'user#1234'
        })
        self.assertFormError(response.context['form'], 'nickname', 'Цей нікнейм вже зайнятий.')

    def test_profile_edit_own_nickname_success(self):
        """Можна зберегти профіль, не змінюючи свій нікнейм (немає колізії з самим собою)"""
        self.client.force_login(self.user)
        response = self.client.post(reverse('profile'), {
            'nickname': 'user_nick',
            'full_name': 'New Name',
            'discord_tag': 'user#1234'
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, 'New Name')