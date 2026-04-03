from rest_framework.test import APITestCase
from rest_framework import status
from .models import User, Round, Tournament
from django.utils import timezone

class ActiveRoundAPITest(APITestCase):
    def setUp(self):
        # Створюємо адміна для авторизації, як вказано в README 
        self.user = User.objects.create_superuser(
            email='admin@example.com', 
            password='Admin123!'
        )
        self.tournament = Tournament.objects.create(title="API Test")
        self.round = Round.objects.create(
            tournament=self.tournament,
            title="Active Round",
            evaluation_criteria="Test Criteria",
            start_time=timezone.now() - timezone.timedelta(hours=1),
            end_time=timezone.now() + timezone.timedelta(hours=1)
        )
        # Отримуємо токен (якщо використовується JWT, як у requirements.txt )
        self.client.force_authenticate(user=self.user)

    def test_active_round_returns_criteria(self):
        """Перевірка, що API віддає поле evaluation_criteria"""
        url = '/api/rounds/active/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('evaluation_criteria', response.data)
        self.assertEqual(response.data['evaluation_criteria'], "Test Criteria")