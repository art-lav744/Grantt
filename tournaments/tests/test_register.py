from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from tournaments.models import User, UserRole


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class RegisterTest(TestCase):
    def test_register_success(self):
        response = self.client.post(reverse('register'), {
            'email': 'newuser@gmail.com',
            'nickname': 'newuser',
            'role': 'team',
            'password1': 'Test1234!',
            'password2': 'Test1234!',
        })
        self.assertRedirects(response, reverse('login'))
        user = User.objects.get(email='newuser@gmail.com')
        self.assertEqual(user.role, UserRole.CAPTAIN)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['newuser@gmail.com'])

    def test_register_duplicate_email(self):
        User.objects.create_user(
            email='existing@gmail.com',
            password='Test1234!',
            nickname='existing',
        )
        response = self.client.post(reverse('register'), {
            'email': 'existing@gmail.com',
            'nickname': 'newuser',
            'role': 'team',
            'password1': 'Test1234!',
            'password2': 'Test1234!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Користувач з таким email вже існує.')

    def test_register_password_mismatch(self):
        response = self.client.post(reverse('register'), {
            'email': 'newuser@gmail.com',
            'nickname': 'newuser',
            'role': 'team',
            'password1': 'Test1234!',
            'password2': 'Wrong1234!',
        })
        self.assertEqual(response.status_code, 200)
