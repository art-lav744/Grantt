from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models, transaction
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
    hide_teams_until_registration_end = models.BooleanField(default=False)
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
        super().clean()
        self.email = (self.email or '').strip().lower()
        if not self.team_id:
            return

        same_tournament_members = TeamMember.objects.filter(
            team__tournament_id=self.team.tournament_id,
            email__iexact=self.email,
        )
        if self.pk:
            same_tournament_members = same_tournament_members.exclude(pk=self.pk)
        if self.email and same_tournament_members.exists():
            raise ValidationError({'email': 'Учасник з таким email вже є в іншій команді цього турніру.'})

        if self.user_id:
            same_tournament_users = TeamMember.objects.filter(
                team__tournament_id=self.team.tournament_id,
                user_id=self.user_id,
            )
            if self.pk:
                same_tournament_users = same_tournament_users.exclude(pk=self.pk)
            if same_tournament_users.exists():
                raise ValidationError({'user': 'Цей користувач вже є в команді цього турніру.'})

    def save(self, *args, **kwargs):
        self.email = (self.email or '').strip().lower()
        self.full_clean()
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
    DEFAULT_CRITERIA = (
        {'name': 'Technical', 'max_score': 100},
        {'name': 'Functionality', 'max_score': 100},
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

    @classmethod
    def parse_criteria_definition(cls, raw_value):
        if raw_value in (None, ''):
            return []

        if isinstance(raw_value, str):
            parsed = []
            for line in raw_value.splitlines():
                normalized = line.strip()
                if not normalized:
                    continue
                if '|' in normalized:
                    name_part, max_part = normalized.rsplit('|', 1)
                else:
                    name_part, max_part = normalized, '100'
                name = name_part.strip(' -:\t')
                if not name:
                    raise ValidationError('Назва критерію не може бути порожньою.')
                try:
                    max_score = float(max_part.strip())
                except (TypeError, ValueError) as exc:
                    raise ValidationError(f'Некоректний максимум для критерію "{name}".') from exc
                parsed.append({'name': name, 'max_score': max_score})
            return parsed

        if isinstance(raw_value, (list, tuple)):
            parsed = []
            for item in raw_value:
                if isinstance(item, dict):
                    name = str(item.get('name', '')).strip()
                    max_score = item.get('max_score', 100)
                else:
                    name = str(item).strip()
                    max_score = 100
                if not name:
                    raise ValidationError('Назва критерію не може бути порожньою.')
                try:
                    max_score = float(max_score)
                except (TypeError, ValueError) as exc:
                    raise ValidationError(f'Некоректний максимум для критерію "{name}".') from exc
                parsed.append({'name': name, 'max_score': max_score})
            return parsed

        raise ValidationError('Непідтримуваний формат критеріїв оцінювання.')

    @classmethod
    def validate_criteria_payload(cls, criteria):
        if not criteria:
            raise ValidationError('Додайте щонайменше один критерій оцінювання.')

        normalized = []
        seen = set()
        for item in criteria:
            name = str(item['name']).strip()
            max_score = float(item['max_score'])
            if not name:
                raise ValidationError('Назва критерію не може бути порожньою.')
            if name.lower() in seen:
                raise ValidationError(f'Критерій "{name}" дублюється.')
            if max_score <= 0:
                raise ValidationError(f'Максимальний бал для "{name}" має бути більшим за 0.')
            seen.add(name.lower())
            normalized.append({'name': name, 'max_score': max_score})
        return normalized

    @classmethod
    def format_criteria_definition(cls, criteria):
        lines = []
        for item in criteria:
            max_score = float(item['max_score'])
            rendered_max = int(max_score) if max_score.is_integer() else max_score
            lines.append(f"{item['name']} | {rendered_max}")
        return '\n'.join(lines)

    def get_or_create_scoring_criteria(self):
        existing = list(self.criteria.order_by('order', 'id'))
        if existing:
            return existing

        parsed = self.parse_criteria_definition(self.evaluation_criteria)
        if not parsed:
            parsed = list(self.DEFAULT_CRITERIA)
            self.evaluation_criteria = self.format_criteria_definition(parsed)
            self.save(update_fields=['evaluation_criteria'])

        normalized = self.validate_criteria_payload(parsed)
        with transaction.atomic():
            created = []
            for index, item in enumerate(normalized):
                created.append(RoundCriterion.objects.create(
                    round=self,
                    name=item['name'],
                    max_score=item['max_score'],
                    order=index,
                ))
        return created

    def set_scoring_criteria(self, raw_criteria):
        parsed = self.parse_criteria_definition(raw_criteria)
        normalized = self.validate_criteria_payload(parsed)
        self.evaluation_criteria = self.format_criteria_definition(normalized)
        if not self.pk:
            return normalized

        self.save(update_fields=['evaluation_criteria'])
        with transaction.atomic():
            self.criteria.all().delete()
            created = []
            for index, item in enumerate(normalized):
                created.append(RoundCriterion.objects.create(
                    round=self,
                    name=item['name'],
                    max_score=item['max_score'],
                    order=index,
                ))
        return created

    def total_max_score(self):
        return sum(criterion.max_score for criterion in self.get_or_create_scoring_criteria())

    def __str__(self):
        return f'{self.tournament.title}: {self.title}'


class RoundCriterion(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='criteria')
    name = models.CharField(max_length=255)
    max_score = models.FloatField(validators=[MinValueValidator(0.01)])
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        constraints = [
            models.UniqueConstraint(fields=['round', 'name'], name='unique_round_criterion_name'),
        ]

    def __str__(self):
        return f'{self.round.title}: {self.name}'


class SubmissionStatus(models.TextChoices):
    PENDING = 'pending', 'Очікує оцінювання'
    EVALUATED = 'evaluated', 'Оцінено'


class Submission(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='submissions')
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='submissions')
    github_link = models.URLField()
    video_link = models.URLField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def status(self):
        return SubmissionStatus.EVALUATED if hasattr(self, 'evaluation') and self.evaluation.is_scored() else SubmissionStatus.PENDING

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
        try:
            evaluation = self.evaluation
        except Evaluation.DoesNotExist:
            evaluation = None

        if not evaluation:
            return {
                'criteria': [],
                'criteria_avg_map': {},
                'raw_total': None,
                'max_total': self.round.total_max_score(),
                'total': None,
            }

        criteria = self.round.get_or_create_scoring_criteria()
        evaluation.ensure_score_entries(criteria)

        criteria_avg_map = {}
        criteria_payload = []
        for criterion in criteria:
            criterion_score = evaluation.criteria_scores.filter(criterion=criterion).first()
            score = criterion_score.score if criterion_score else 0.0
            criteria_avg_map[criterion.name] = score
            criteria_payload.append({
                'id': criterion.id,
                'name': criterion.name,
                'max_score': criterion.max_score,
                'average': score,
            })

        max_total = sum(criterion.max_score for criterion in criteria)
        raw_total = evaluation.total_score()
        total = (raw_total / max_total * 100) if max_total else 0.0

        return {
            'criteria': criteria_payload,
            'criteria_avg_map': criteria_avg_map,
            'raw_total': raw_total,
            'max_total': max_total,
            'total': total,
        }


class Evaluation(models.Model):
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name='evaluation')
    jury = models.ForeignKey(User, on_delete=models.CASCADE, related_name='evaluations')
    comment = models.TextField(blank=True, default='', verbose_name='Коментар')
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def status(self):
        return SubmissionStatus.EVALUATED if hasattr(self, 'evaluation') and self.evaluation.is_scored() else SubmissionStatus.PENDING

    class Meta:
        unique_together = [('submission',)]

    def ensure_score_entries(self, criteria=None):
        criteria = criteria or self.submission.round.get_or_create_scoring_criteria()
        existing_ids = set(self.criteria_scores.values_list('criterion_id', flat=True))
        missing = [
            EvaluationCriterionScore(evaluation=self, criterion=criterion, score=0)
            for criterion in criteria
            if criterion.id not in existing_ids
        ]
        if missing:
            EvaluationCriterionScore.objects.bulk_create(missing)
        return list(self.criteria_scores.select_related('criterion').order_by('criterion__order', 'criterion__id'))

    def total_score(self):
        return sum(item.score for item in self.ensure_score_entries())

    def is_scored(self):
        return any(item.score > 0 for item in self.ensure_score_entries())


class EvaluationCriterionScore(models.Model):
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='criteria_scores')
    criterion = models.ForeignKey(RoundCriterion, on_delete=models.CASCADE, related_name='evaluation_scores')
    score = models.FloatField(default=0, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ['criterion__order', 'criterion__id', 'id']
        constraints = [
            models.UniqueConstraint(fields=['evaluation', 'criterion'], name='unique_evaluation_criterion_score'),
        ]

    def clean(self):
        super().clean()
        if self.criterion and self.evaluation and self.criterion.round_id != self.evaluation.submission.round_id:
            raise ValidationError('Критерій має належати раунду цієї оцінки.')
        if self.criterion and self.score > self.criterion.max_score:
            raise ValidationError({'score': f'Оцінка не може перевищувати {self.criterion.max_score}.'})


class JuryRegistrationStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'


class JuryTournamentRegistration(models.Model):
    jury = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='jury_registration_requests',
    )
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='jury_registration_requests',
    )
    status = models.CharField(
        max_length=20,
        choices=JuryRegistrationStatus.choices,
        default=JuryRegistrationStatus.PENDING,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_jury_requests',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('jury', 'tournament')]
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f'{self.jury.email} -> {self.tournament.title} ({self.status})'
