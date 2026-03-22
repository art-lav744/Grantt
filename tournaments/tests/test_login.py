from django.test import TestCase
from django.urls import reverse

from tournaments.models import User


class LoginTest(TestCase):
    def setUp(self):
        self.user_verified = User.objects.create_user(
            email='verified@gmail.com',
            password='Test1234!',
            nickname='verified',
            is_verified=True,
        )
        self.user_unverified = User.objects.create_user(
            email='unverified@gmail.com',
            password='Test1234!',
            nickname='unverified',
            is_verified=False,
        )

    def test_login_verified_user(self):
        response = self.client.post(reverse('login'), {
            'username': 'verified@gmail.com',
            'password': 'Test1234!',
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_unverified_user(self):
        response = self.client.post(reverse('login'), {
            'username': 'unverified@gmail.com',
            'password': 'Test1234!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Спочатку підтвердіть email.')

    def test_login_wrong_password(self):
        response = self.client.post(reverse('login'), {
            'username': 'verified@gmail.com',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
