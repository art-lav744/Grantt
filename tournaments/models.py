from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.conf import settings
from django.utils import timezone


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Адміністратор'
    ORGANIZER = 'organizer', 'Організатор'
    JURY = 'jury', 'Журі'
    PARTICIPANT = 'participant', 'Учасник'


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('role', UserRole.PARTICIPANT)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.ADMIN)
        extra_fields.setdefault('is_verified', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    first_name = None
    last_name = None

    email = models.EmailField(unique=True)
    nickname = models.CharField(max_length=150, unique=True)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.PARTICIPANT)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    full_name = models.CharField(max_length=255, verbose_name="ПІБ", blank=True, null=True)
    discord_tag = models.CharField(max_length=255, blank=True, null=True, verbose_name="Discord тег")
    jury_tournaments = models.ManyToManyField('Tournament', related_name='jury_members', blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nickname', 'full_name']

    objects = UserManager()

    def __str__(self):
        return self.email


class TournamentStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    REGISTRATION = 'registration', 'Registration'
    OPEN = 'open', 'Open'
    CLOSED = 'closed', 'Closed'
    ARCHIVED = 'archived', 'Archived'


class Tournament(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=TournamentStatus.choices,
        default=TournamentStatus.DRAFT,
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='tournaments',
        null=True,
        blank=True,
    )

    # Період реєстрації
    reg_start = models.DateTimeField()
    reg_end = models.DateTimeField()

    # Період проведення (саме тоді команди здають роботи)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    max_teams = models.PositiveIntegerField(default=10)
    max_team_members = models.PositiveIntegerField(default=5)
    min_team_members = models.PositiveIntegerField(default=2)
    cover_image = models.ImageField(upload_to='tournaments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def logical_status(self):
        now = timezone.now()
        # Якщо адмін тримає в чернетці або примусово завершив — повертаємо це
        if self.status in ['Draft', 'Finished']:
            return self.status
        
        if now < self.reg_start:
            return 'Scheduled'  # Відображається як запланований
        elif self.reg_start <= now <= self.reg_end:
            return 'Registration'
        elif self.reg_end < now <= self.end_time:
            return 'Running'
        else:
            return 'Finished'

    def __str__(self):
        return self.title


class Team(models.Model):
    name = models.CharField(max_length=100)  # Перевірка унікальності імені в межах турніру буде через unique_together
    tournament = models.ForeignKey(
        Tournament, 
        on_delete=models.CASCADE, 
        related_name='teams'
    )
    captain = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='managed_teams',
        null=True,
        blank=True,
    )
    captain_email = models.EmailField(blank=True, default='')
    captain_name = models.CharField(max_length=255, blank=True, default='')
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='TeamMember',
        related_name='teams_membership',
    )# Використовуємо проміжну модель TeamMember

    organization = models.CharField(
            max_length=255,
            blank=True,
            null=True,
            verbose_name="Місто / школа / організація")

    class Meta:
        unique_together = [('tournament', 'name'), ('tournament', 'captain')]
    
    def __str__(self):
        return self.name


class TeamMember(models.Model):
    team = models.ForeignKey(
        'Team', 
        on_delete=models.CASCADE, 
        related_name='memberships'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='team_participations'
    )
    # Вимоги ТЗ: ПІБ та Email учасника [cite: 13]
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Валідація: Email унікальні в межах однієї команди [cite: 13]
        unique_together = ('team', 'email')

    def __str__(self):
        return f'{self.full_name} ({self.email})'


class Round(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='rounds')
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, default='Draft')

    def __str__(self):
        return f'{self.tournament.title}: {self.title}'


class Submission(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='submissions')
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='submissions')
    github_link = models.URLField()
    video_link = models.URLField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('team', 'round')]


class Evaluation(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='evaluations')
    jury = models.ForeignKey(User, on_delete=models.CASCADE, related_name='evaluations')
    comment = models.TextField(blank=True, default='', verbose_name='Коментар')
    tech_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    func_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('submission', 'jury')]
