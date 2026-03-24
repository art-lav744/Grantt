from django.test import TestCase
from django.urls import reverse
from tournaments.models import User


class LoginTest(TestCase):

    def setUp(self):
        # створюємо верифікованого користувача якого використовуємо в тестах
        self.user_verified = User.objects.create_user(
            email='verified@gmail.com',
            password='Test1234!',
            nickname='verified',
            is_verified=True,
        )
        # створюємо користувача без підтвердження email
        self.user_unverified = User.objects.create_user(
            email='unverified@gmail.com',
            password='Test1234!',
            nickname='unverified',
            is_verified=False,
        )

    def test_login_verified_user(self):
        # верифікований користувач з правильним паролем
        # має успішно залогінитись і перенаправитись на dashboard
        response = self.client.post(reverse('login'), {
            'username': 'verified@gmail.com',
            'password': 'Test1234!',
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_unverified_user(self):
        # неверифікований користувач не повинен мати змогу залогінитись
        # сторінка має повернутись з помилкою
        response = self.client.post(reverse('login'), {
            'username': 'unverified@gmail.com',
            'password': 'Test1234!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Спочатку підтвердіть email.')

    def test_login_wrong_password(self):
        # користувач з неправильним паролем не повинен залогінитись
        # сторінка має залишитись на формі логіну
        response = self.client.post(reverse('login'), {
            'username': 'verified@gmail.com',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)