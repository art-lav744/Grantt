from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from ..models import Team, TeamInvite, UserNotification, TeamMember, Tournament

User = get_user_model()

class TeamInvitationTests(TestCase):
    def setUp(self):
        # 1. Створюємо тестових користувачів
        self.captain = User.objects.create_user(
            email='captain@example.com', 
            password='password123',
            nickname='Captain'
        )
        self.invited_user = User.objects.create_user(
            email='member@example.com', 
            password='password123',
            nickname='Member'
        )

        # 2. СТВОРЮЄМО ТУРНІР З УСІМА ОБОВ'ЯЗКОВИМИ ПОЛЯМИ
        now = timezone.now()
        self.tournament = Tournament.objects.create(
            title="Тестовий турнір",
            description="Опис",
            reg_start=now,
            reg_end=now + timedelta(days=1),
            start_time=now + timedelta(days=2),
            end_time=now + timedelta(days=3)
        )
        
        # 3. Створюємо команду
        self.team = Team.objects.create(
            name="Test Team",
            captain=self.captain,
            tournament=self.tournament
        )
        
        self.client = Client()

    def test_send_invite_action(self):
        """Перевірка створення запрошення, сповіщення та відправки Email"""
        self.client.login(email='captain@example.com', password='password123')
        
        url = reverse('send_invite_action', args=[self.team.id])
        data = {'email': 'member@example.com'}
        
        response = self.client.post(url, data)
        
        # Перевіряємо редірект назад до деталей команди
        self.assertEqual(response.status_code, 302)
        
        # Перевіряємо, чи створився об'єкт запрошення в БД
        self.assertTrue(TeamInvite.objects.filter(email='member@example.com', team=self.team).exists())
        
        # Перевіряємо, чи створилося внутрішнє сповіщення для юзера
        self.assertTrue(UserNotification.objects.filter(user=self.invited_user).exists())
        
        # Перевіряємо, чи було відправлено 1 лист (імітація Gmail)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Запрошення до команди", mail.outbox[0].subject)

    def test_process_invite_link_success(self):
        """Перевірка успішного прийняття запрошення через посилання"""
        # Створюємо запрошення вручну для тесту
        invite = TeamInvite.objects.create(
            team=self.team,
            email='member@example.com',
            inviter=self.captain
        )
        
        # Логінимося під запрошеним користувачем
        self.client.login(email='member@example.com', password='password123')
        
        url = reverse('process_invite_link', args=[invite.id])
        response = self.client.get(url)
        
        # Перевіряємо редірект на дашборд
        self.assertEqual(response.status_code, 302)
        
        # Перевіряємо, чи став юзер учасником команди
        self.assertTrue(TeamMember.objects.filter(team=self.team, user=self.invited_user).exists())
        
        # Перевіряємо, чи деактивувалося запрошення
        invite.refresh_from_db()
        self.assertFalse(invite.is_active)

    def test_invite_wrong_user_access(self):
        """Перевірка безпеки: користувач не може прийняти чуже запрошення"""
        invite = TeamInvite.objects.create(
            team=self.team,
            email='member@example.com', # призначено для member@...
            inviter=self.captain
        )
        
        # Створюємо іншого лівого юзера
        hacker = User.objects.create_user(email='hacker@example.com', password='password123')
        self.client.login(email='hacker@example.com', password='password123')
        
        url = reverse('process_invite_link', args=[invite.id])
        response = self.client.get(url)
        
        # Перевіряємо, що запис у TeamMember НЕ створився
        self.assertFalse(TeamMember.objects.filter(team=self.team, user=hacker).exists())
        
        # Перевіряємо, що інвайт залишився активним
        invite.refresh_from_db()
        self.assertTrue(invite.is_active)

    def test_notification_creation_for_new_user(self):
        """Перевірка, що для незареєстрованого юзера сповіщення в системі не створюється (тільки Email)"""
        self.client.login(email='captain@example.com', password='password123')
        
        url = reverse('send_invite_action', args=[self.team.id])
        data = {'email': 'unknown@gmail.com'}
        
        self.client.post(url, data)
        
        # В БД має бути 0 сповіщень для неіснуючих юзерів
        self.assertEqual(UserNotification.objects.count(), 0)
        # Але лист має піти
        self.assertEqual(len(mail.outbox), 1)