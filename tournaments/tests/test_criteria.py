from django.test import TestCase
from django.utils import timezone
from ..models import Round, Tournament

class RoundModelTest(TestCase):
    def setUp(self):
        # Створюємо таймстемп для обов'язкових полів
        now = timezone.now()
        # Створюємо турнір з усіма обов'язковими датами
        self.tournament = Tournament.objects.create(
            title="Test Tournament",
            reg_start=now,
            reg_end=now + timezone.timedelta(days=7),
            start_time=now + timezone.timedelta(days=8),
            end_time=now + timezone.timedelta(days=10)
        )

    def test_round_evaluation_criteria_save(self):
        """Перевірка, що критерії зберігаються і читаються з БД"""
        criteria_text = "1. Logic: 10 points\n2. Style: 5 points"
        test_round = Round.objects.create(
            tournament=self.tournament,
            title="Final Round",
            description="Test Desc",
            requirements="Test Req",
            evaluation_criteria=criteria_text,
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=2)
        )
        
        saved_round = Round.objects.get(id=test_round.id)
        self.assertEqual(saved_round.evaluation_criteria, criteria_text)
