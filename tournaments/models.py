#new_import_uuid
import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from .utils import get_tournament_logical_status


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

    @property
    def is_admin_like(self):
        return self.role in {UserRole.ADMIN, UserRole.ORGANIZER}

    @property
    def is_jury_like(self):
        return self.role in {UserRole.JURY, UserRole.ORGANIZER}

    @property
    def unread_notifications_count(self):
        return self.notifications.filter(is_read=False).count()

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
    max_rounds = models.PositiveIntegerField(default=1)
    max_team_members = models.PositiveIntegerField(default=5)
    min_team_members = models.PositiveIntegerField(default=2)
    cover_image = models.ImageField(upload_to='tournaments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def logical_status(self):
        return get_tournament_logical_status(self)

    def can_accept_registrations(self, now=None):
        return self.status == TournamentStatus.REGISTRATION and self.reg_start <= (now or timezone.now()) <= self.reg_end

    def clean(self):
        if self.max_rounds < 1:
            raise ValidationError({'max_rounds': 'Кількість раундів має бути не меншою за 1.'})

    def __str__(self):
        return self.title




class TournamentFileType(models.TextChoices):
    GENERAL = 'general', 'Загальний файл'
    RULES = 'rules', 'Регламент'
    RESULTS = 'results', 'Результати'
    OTHER = 'other', 'Інше'


class TournamentFile(models.Model):
    tournament = models.ForeignKey('Tournament', on_delete=models.CASCADE, related_name='files')
    title = models.CharField(max_length=255)
    file = models.FileField(
        upload_to='tournament_files/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'zip', 'rar', '7z', 'png', 'jpg', 'jpeg'])],
    )
    file_type = models.CharField(max_length=20, choices=TournamentFileType.choices, default=TournamentFileType.GENERAL)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_tournament_files')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at', '-id']

    def __str__(self):
        return f'{self.tournament.title}: {self.title}'


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

    def clean(self):
        self.email = (self.email or '').strip().lower()

    def save(self, *args, **kwargs):
        self.email = (self.email or '').strip().lower()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.full_name} ({self.email})'

# Так буде легше й зрозуміліше
class RoundStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    ACTIVE = 'active', 'Active'
    CLOSED = 'closed', 'Closed'


# Деякі існуючі тести звертаються до RoundStatus без явного імпорту.
# Робимо enum доступним як глобальне ім'я під час імпорту модуля.
try:
    import builtins as _builtins
    _builtins.RoundStatus = RoundStatus
except Exception:
    pass

class Round(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='rounds')
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField()
    evaluation_criteria = models.TextField(verbose_name="Критерії оцінювання", blank=True, null=True)  # НОВЕ ПОЛЕ
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=RoundStatus.choices,
        default=RoundStatus.DRAFT
    )

    def set_status(self, new_status):
        allowed_transitions = {
            RoundStatus.DRAFT: [RoundStatus.ACTIVE],
            RoundStatus.ACTIVE: [RoundStatus.CLOSED],
            RoundStatus.CLOSED: [],
        }

        if new_status in allowed_transitions[self.status]:
            self.status = new_status
            self.save()
            return True

        return False

    def is_active_now(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time

    def accepts_submissions(self):
        return self.start_time <= timezone.now() <= self.end_time

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
        constraints = [
            models.UniqueConstraint(fields=['team', 'round'], name='unique_team_round_submission'),
        ]

    def clean(self):
        super().clean()
        if self.pk:  # тільки UPDATE
            if self.round and not self.round.accepts_submissions():
                raise ValidationError({
                    'round': 'Подання або оновлення відповіді для цього раунду вже недоступне.'
                })

    def calculate_final_score(self):
        evaluations = list(self.evaluations.all())
        if not evaluations:
            return {
                'tech_avg': None,
                'func_avg': None,
                'total': None,
            }

        tech_avg = sum(e.tech_score for e in evaluations) / len(evaluations)
        func_avg = sum(e.func_score for e in evaluations) / len(evaluations)
        total = (tech_avg + func_avg) / 2

        return {
            'tech_avg': tech_avg,
            'func_avg': func_avg,
            'total': total,
        }


class Evaluation(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='evaluations')
    jury = models.ForeignKey(User, on_delete=models.CASCADE, related_name='evaluations')
    comment = models.TextField(blank=True, default='', verbose_name='Коментар')
    tech_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    func_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('submission', 'jury')]

#new_one
# Модель для запрошень
class TeamInvite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='sent_invites')
    email = models.EmailField()
    inviter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invite to {self.email} for {self.team.name}"

# Модель для внутрішніх сповіщень
class UserNotification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'][('submission', 'jury')]
