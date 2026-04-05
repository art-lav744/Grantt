from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from ..models import User, Round, Tournament, Team, TeamMember

class ActiveRoundAPITest(APITestCase):
    def setUp(self):
        now = timezone.now()
        
        # 1. Створюємо користувача (тільки поля, що є в models.py)
        self.user = User.objects.create_user(
            email='student_test@example.com', 
            password='Password123!',
            nickname='tester'
        )
        
        # 2. Створюємо турнір
        self.tournament = Tournament.objects.create(
            title="API Test Tournament",
            reg_start=now - timezone.timedelta(days=2),
            reg_end=now + timezone.timedelta(days=5),
            start_time=now - timezone.timedelta(days=1),
            end_time=now + timezone.timedelta(days=10),
            status='Active' # Важливо для логіки деяких в'юшок
        )
        
        # 3. Створюємо команду
        self.team = Team.objects.create(
            name="Alpha Team",
            tournament=self.tournament
        )

        # 4. ПРИВ'ЯЗКА: Створюємо запис у TeamMember (це виправить 404)
        TeamMember.objects.create(
            team=self.team,
            email=self.user.email,
            full_name="Test Student"
        )
        
        # 5. Створюємо активний раунд зі статусом 'Active'
        # У вашій views.py стоїть фільтр .filter(status='Active')
        self.round = Round.objects.create(
            tournament=self.tournament,
            title="Active Round",
            description="Test Desc",
            requirements="Test Req",
            evaluation_criteria="1. Технічна частина\n2. Креативність",
            start_time=now - timezone.timedelta(hours=1),
            end_time=now + timezone.timedelta(hours=5),
            status=RoundStatus.ACTIVE
        )
        
        # 6. Авторизація
        self.client.force_authenticate(user=self.user)

    def test_active_round_returns_criteria(self):
        """Перевірка отримання критеріїв через ActiveTaskView"""
        url = '/api/rounds/active/'
        response = self.client.get(url)
        
        # Виводимо дані для діагностики
        print(f"\nDEBUG DATA: {response.data}") 
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('evaluation_criteria', response.data)
        self.assertEqual(
            response.data['evaluation_criteria'], 
            "1. Технічна частина\n2. Креативність"
        )
