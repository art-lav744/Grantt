from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from tournaments.models import User

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class RegisterTest(TestCase):

    def test_register_success(self):
        response = self.client.post(reverse('register'), {
            'email': 'newuser@test.com',
            'nickname': 'newuser',
            'role': 'team',
            'password1': 'Test1234!',
            'password2': 'Test1234!',
        })
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(email='newuser@test.com').exists())
        # перевіряємо що лист був відправлений але не реально а в памʼять
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['newuser@test.com'])

    def test_register_duplicate_email(self):
        # якщо email вже існує в базі — реєстрація має провалитись
        # сторінка повертається з помилкою валідації
        User.objects.create_user(
            email='existing@test.com',
            password='Test1234!',
            nickname='existing',
        )
        response = self.client.post(reverse('register'), {
            'email': 'existing@test.com',
            'nickname': 'newuser',
            'role': 'team',
            'password1': 'Test1234!',
            'password2': 'Test1234!',
        })
        self.assertEqual(response.status_code, 200)

    def test_register_password_mismatch(self):
        # якщо паролі не співпадають — реєстрація має провалитись
        # сторінка повертається з помилкою валідації
        response = self.client.post(reverse('register'), {
            'email': 'newuser@test.com',
            'nickname': 'newuser',
            'role': 'team',
            'password1': 'Test1234!',
            'password2': 'Wrong1234!',
        })
        self.assertEqual(response.status_code, 200)