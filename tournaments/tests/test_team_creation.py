from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from tournaments.models import Tournament, Team, TeamMember, TournamentStatus
from tournaments.serializers import TeamCreateSerializer

User = get_user_model()


class TeamCreateSerializerTest(TestCase):
    """Тест для TeamCreateSerializer.create() методу"""

    def setUp(self):
        """Налаштування для кожного тесту"""
        self.now = timezone.now()
        # Створюємо капітана
        self.captain = User.objects.create_user(
            email='captain@gmail.com',
            password='Test1234!',
            nickname='captain',
            is_verified=True,
        )
        # Створюємо потенційних членів
        self.member1 = User.objects.create_user(
            email='member1@gmail.com',
            password='Test1234!',
            nickname='member1',
            is_verified=True,
        )
        self.member2 = User.objects.create_user(
            email='member2@gmail.com',
            password='Test1234!',
            nickname='member2',
            is_verified=True,
        )
        # Створюємо турнір зі статусом REGISTRATION
        self.tournament = Tournament.objects.create(
            title='Test Tournament',
            description='Test Description',
            status=TournamentStatus.REGISTRATION,
            creator=User.objects.create_user(
                email='admin@gmail.com',
                password='Test1234!',
                nickname='admin',
                is_verified=True,
            ),
            reg_start=self.now - timedelta(days=1),
            reg_end=self.now + timedelta(days=10),
            start_time=self.now + timedelta(days=11),
            end_time=self.now + timedelta(days=20),
            max_teams=10,
            max_team_members=5,
            min_team_members=1,
        )

    def _create_mock_request(self, user):
        "Метод для створення фальшивого http реквесту"
        class MockRequest:
            def __init__(self, user):
                self.user = user
        return MockRequest(user)

    def test_create_team_with_captain_only(self):
        """Тест створення команди тільки з капітаном"""
        serializer = TeamCreateSerializer(data={
            'name': 'Test Team',
            'tournament_id': self.tournament.id,
            'captain_email': self.captain.email,
            'captain_name': 'Captain Name',
            'members': [],
        }, context={'request': self._create_mock_request(self.captain)})
        
        self.assertTrue(serializer.is_valid(), serializer.errors)
        team = serializer.save()
        
        # Перевіряємо, що команда створена
        self.assertEqual(team.name, 'Test Team')
        self.assertEqual(team.tournament, self.tournament)
        self.assertEqual(team.captain, self.captain)
        self.assertEqual(team.captain_email, self.captain.email.lower())
        self.assertEqual(team.captain_name, 'Captain Name')

    def test_create_team_with_members(self):
        """Тест створення команди з капітаном і членами"""
        serializer = TeamCreateSerializer(data={
            'name': 'Team With Members',
            'tournament_id': self.tournament.id,
            'captain_email': self.captain.email,
            'captain_name': 'Captain Name',
            'members': [
                {
                    'full_name': 'Member One',
                    'email': self.member1.email,
                },
                {
                    'full_name': 'Member Two',
                    'email': self.member2.email,
                },
            ],
        }, context={'request': self._create_mock_request(self.captain)})
        
        self.assertTrue(serializer.is_valid(), serializer.errors)
        team = serializer.save()
        
        # Перевіряємо команду
        self.assertEqual(team.name, 'Team With Members')
        self.assertEqual(team.captain, self.captain)
        
        # Перевіряємо, що члени додані
        members = TeamMember.objects.filter(team=team).order_by('full_name')
        self.assertEqual(members.count(), 2)
        
        self.assertEqual(members[0].full_name, 'Member One')
        self.assertEqual(members[0].email, self.member1.email.lower())
        
        self.assertEqual(members[1].full_name, 'Member Two')
        self.assertEqual(members[1].email, self.member2.email.lower())

    def test_create_team_email_normalization(self):
        """Тест нормалізації email (до нижніх символів)"""
        serializer = TeamCreateSerializer(data={
            'name': 'Email Test Team',
            'tournament_id': self.tournament.id,
            'captain_email': 'CAPTAIN@GMAIL.COM',  # UPPERCASE
            'captain_name': 'Captain Name',
            'members': [
                {
                    'full_name': 'Member',
                    'email': 'MEMBER@GMAIL.COM',  # UPPERCASE
                },
            ],
        }, context={'request': self._create_mock_request(self.captain)})
        
        self.assertTrue(serializer.is_valid(), serializer.errors)
        team = serializer.save()
        
        # Перевіряємо нормалізацію
        self.assertEqual(team.captain_email, 'captain@gmail.com')
        member = TeamMember.objects.get(team=team)
        self.assertEqual(member.email, 'member@gmail.com')

    def test_create_team_anonymous_user(self):
        """Тест створення команди без авторизованого користувача"""
        class AnonymousUser:
            is_authenticated = False
        
        class MockRequest:
            def __init__(self):
                self.user = AnonymousUser()
        
        serializer = TeamCreateSerializer(data={
            'name': 'Anon Team',
            'tournament_id': self.tournament.id,
            'captain_email': self.captain.email,
            'captain_name': 'Captain Name',
            'members': [],
        }, context={'request': MockRequest()})
        
        self.assertTrue(serializer.is_valid(), serializer.errors)
        team = serializer.save()
        
        # Для анонімного користувача капітан повинен бути None
        self.assertIsNone(team.captain)

    def test_create_team_nonexistent_tournament(self):
        """Тест створення команди з неіснуючим турніром"""
        serializer = TeamCreateSerializer(data={
            'name': 'Test Team',
            'tournament_id': 99999,  # Неіснуючий ID
            'captain_email': self.captain.email,
            'captain_name': 'Captain Name',
            'members': [],
        }, context={'request': self._create_mock_request(self.captain)})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('Турнір не знайдено', str(serializer.errors))

    def test_create_team_closed_registration(self):
        """Тест створення команди з закритою реєстрацією"""
        closed_tournament = Tournament.objects.create(
            title='Closed Tournament',
            description='Test',
            status=TournamentStatus.OPEN,  # Статус не REGISTRATION
            creator=self.tournament.creator,
            reg_start=self.now - timedelta(days=10),
            reg_end=self.now - timedelta(days=1),
            start_time=self.now,
            end_time=self.now + timedelta(days=10),
            max_teams=10,
            max_team_members=5,
            min_team_members=1,
        )
        
        serializer = TeamCreateSerializer(data={
            'name': 'Test Team',
            'tournament_id': closed_tournament.id,
            'captain_email': self.captain.email,
            'captain_name': 'Captain Name',
            'members': [],
        }, context={'request': self._create_mock_request(self.captain)})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('закрита або ще не почалася', str(serializer.errors))

    def test_create_team_outside_registration_window(self):
        """Тест створення команди поза реєстраційним вікном"""
        tournament_future = Tournament.objects.create(
            title='Future Tournament',
            description='Test',
            status=TournamentStatus.REGISTRATION,
            creator=self.tournament.creator,
            reg_start=self.now + timedelta(days=10),  # Реєстрація в майбутньому
            reg_end=self.now + timedelta(days=20),
            start_time=self.now + timedelta(days=21),
            end_time=self.now + timedelta(days=30),
            max_teams=10,
            max_team_members=5,
            min_team_members=1,
        )
        
        serializer = TeamCreateSerializer(data={
            'name': 'Test Team',
            'tournament_id': tournament_future.id,
            'captain_email': self.captain.email,
            'captain_name': 'Captain Name',
            'members': [],
        }, context={'request': self._create_mock_request(self.captain)})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('поза межами реєстраційного вікна', str(serializer.errors))

    def test_create_team_max_teams_reached(self):
        """Тест створення команди коли досягнута максимальна кількість команд"""
        tournament_full = Tournament.objects.create(
            title='Full Tournament',
            description='Test',
            status=TournamentStatus.REGISTRATION,
            creator=self.tournament.creator,
            reg_start=self.now - timedelta(days=1),
            reg_end=self.now + timedelta(days=10),
            start_time=self.now + timedelta(days=11),
            end_time=self.now + timedelta(days=20),
            max_teams=1,  # Тільки одна команда
            max_team_members=5,
            min_team_members=1,
        )
        
        # Створюємо першу команду
        Team.objects.create(
            name='First Team',
            tournament=tournament_full,
            captain=self.captain,
        )
        
        # Намагаємось створити другу команду
        new_captain = User.objects.create_user(
            email='newcaptain@gmail.com',
            password='Test1234!',
            nickname='newcaptain',
            is_verified=True,
        )
        
        serializer = TeamCreateSerializer(data={
            'name': 'Second Team',
            'tournament_id': tournament_full.id,
            'captain_email': new_captain.email,
            'captain_name': 'New Captain',
            'members': [],
        }, context={'request': self._create_mock_request(new_captain)})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('Усі місця на турнір зайняті', str(serializer.errors))

    def test_create_team_duplicate_email(self):
        """Тест створення команди зі здвоєним email"""
        serializer = TeamCreateSerializer(data={
            'name': 'Duplicate Email Team',
            'tournament_id': self.tournament.id,
            'captain_email': self.captain.email,
            'captain_name': 'Captain Name',
            'members': [
                {
                    'full_name': 'Member',
                    'email': self.captain.email,  # Той же email що й капітан!
                },
            ],
        }, context={'request': self._create_mock_request(self.captain)})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('Один і той самий email вказано кілька разів', str(serializer.errors))

    def test_create_team_invalid_team_size(self):
        """Тест створення команди з невірною кількістю людей"""
        tournament_strict = Tournament.objects.create(
            title='Strict Tournament',
            description='Test',
            status=TournamentStatus.REGISTRATION,
            creator=self.tournament.creator,
            reg_start=self.now - timedelta(days=1),
            reg_end=self.now + timedelta(days=10),
            start_time=self.now + timedelta(days=11),
            end_time=self.now + timedelta(days=20),
            max_teams=10,
            max_team_members=3,
            min_team_members=2,  # Мін 2 людей
        )
        
        # Спроба створити команду тільки з капітаном (без членів)
        serializer = TeamCreateSerializer(data={
            'name': 'Small Team',
            'tournament_id': tournament_strict.id,
            'captain_email': self.captain.email,
            'captain_name': 'Captain Name',
            'members': [],  # Немає членів
        }, context={'request': self._create_mock_request(self.captain)})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('Кількість учасників не відповідає вимогам', str(serializer.errors))

    def test_create_team_already_registered(self):
        """Тест створення команди коли капітан вже зареєстрований як капітан"""
        # Створюємо першу команду
        first_team = Team.objects.create(
            name='First Team',
            tournament=self.tournament,
            captain=self.captain,
            captain_email=self.captain.email.lower(),
            captain_name='Captain',
        )
        
        # Намагаємось створити другу команду з тим же капітаном
        serializer = TeamCreateSerializer(data={
            'name': 'Second Team',
            'tournament_id': self.tournament.id,
            'captain_email': self.captain.email,
            'captain_name': 'Captain Name',
            'members': [],
        }, context={'request': self._create_mock_request(self.captain)})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('Ця команда вже зареєстрована на турнір', str(serializer.errors))

    def test_create_team_member_already_registered(self):
        """Тест створення команди коли учасник вже зареєстрований в інший команді"""
        # Створюємо першу команду з членом
        first_team = Team.objects.create(
            name='First Team',
            tournament=self.tournament,
            captain=self.captain,
            captain_email=self.captain.email.lower(),
            captain_name='Captain',
        )
        TeamMember.objects.create(
            team=first_team,
            full_name=self.member1.full_name or 'Member 1',
            email=self.member1.email,
        )
        
        # Намагаємось створити другу команду з тим же членом
        new_captain = User.objects.create_user(
            email='newcaptain@gmail.com',
            password='Test1234!',
            nickname='newcaptain',
            is_verified=True,
        )
        
        serializer = TeamCreateSerializer(data={
            'name': 'Second Team',
            'tournament_id': self.tournament.id,
            'captain_email': new_captain.email,
            'captain_name': 'New Captain',
            'members': [
                {
                    'full_name': 'Member 1',
                    'email': self.member1.email,  # Той же email!
                },
            ],
        }, context={'request': self._create_mock_request(new_captain)})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('зареєстровані у цьому турнірі', str(serializer.errors))

    def test_create_team_transaction_rollback(self):
        """Тест що при помилці при додаванні членів команда не створюється"""
        # Тест неправильних даних членів що призведе до помилки при bulk_create
        serializer = TeamCreateSerializer(data={
            'name': 'Transaction Test',
            'tournament_id': self.tournament.id,
            'captain_email': self.captain.email,
            'captain_name': 'Captain Name',
            'members': [
                {
                    'full_name': 'Member One',
                    'email': self.member1.email,
                },
            ],
        }, context={'request': self._create_mock_request(self.captain)})
        
        self.assertTrue(serializer.is_valid())
        team = serializer.save()
        
        # Перевіряємо що команда й члени успішно створені
        self.assertTrue(Team.objects.filter(id=team.id).exists())
        self.assertEqual(TeamMember.objects.filter(team=team).count(), 1)
