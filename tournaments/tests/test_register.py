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
            'password1': 'Test1234!',
            'password2': 'Test1234!',
        })
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(email='newuser@gmail.com').exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['newuser@gmail.com'])
        self.assertEqual(User.objects.get(email='newuser@gmail.com').role, UserRole.PARTICIPANT)

    def test_register_invalid_domain(self):
        response = self.client.post(reverse('register'), {
            'email': 'newuser@test.com',
            'nickname': 'newuser',
            'password1': 'Test1234!',
            'password2': 'Test1234!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context['form'], 'email',
            'Дозволені лише email на: gmail.com, outlook.com, hotmail.com, '
            'live.com, yahoo.com, icloud.com, ukr.net'
        )
        self.assertFalse(User.objects.filter(email='newuser@test.com').exists())

    def test_register_duplicate_nickname(self):
        User.objects.create_user(
            email='first@gmail.com',
            password='Test1234!',
            nickname='takenname',
        )
        response = self.client.post(reverse('register'), {
            'email': 'second@gmail.com',
            'nickname': 'takenname',
            'password1': 'Test1234!',
            'password2': 'Test1234!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context['form'], 'nickname',
            'Користувач з таким нікнеймом вже існує.'
        )
        self.assertFalse(User.objects.filter(email='second@gmail.com').exists())

    def test_register_duplicate_email(self):
        User.objects.create_user(
            email='existing@gmail.com',
            password='Test1234!',
            nickname='existing',
        )
        response = self.client.post(reverse('register'), {
            'email': 'existing@gmail.com',
            'nickname': 'newuser',
            'password1': 'Test1234!',
            'password2': 'Test1234!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context['form'], 'email',
            'Користувач з таким email вже існує.'
        )

    def test_register_password_mismatch(self):
        response = self.client.post(reverse('register'), {
            'email': 'newuser@gmail.com',
            'nickname': 'newuser',
            'password1': 'Test1234!',
            'password2': 'Wrong1234!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context['form'], 'password2',
            'Паролі не збігаються'
        )

    def test_register_keeps_password_values_on_error(self):
        response = self.client.post(reverse('register'), {
            'email': 'newuser@gmail.com',
            'nickname': 'newuser',
            'password1': 'Test1234!',
            'password2': 'Wrong1234!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="password1" value="Test1234!"', html=False)
        self.assertContains(response, 'name="password2" value="Wrong1234!"', html=False)