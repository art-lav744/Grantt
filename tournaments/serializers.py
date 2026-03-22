from collections import Counter

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.validators import validate_email as django_validate_email
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import serializers

from email_validator import EmailNotValidError, validate_email

from .models import Evaluation, Round, Submission, Team, TeamMember, Tournament, TournamentStatus, User, UserRole
from .utils import contains_cyrillic, create_access_token, validate_password_complexity

TEAM_ROLE_ALIAS = 'team'


class TournamentShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = ('id', 'title', 'status')


class UserOutSerializer(serializers.ModelSerializer):
    tournaments = TournamentShortSerializer(many=True, read_only=True)
    profile_image_path = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'nickname', 'role', 'profile_image_path', 'tournaments')

    def get_profile_image_path(self, obj):
        return obj.profile_image.url if obj.profile_image else None


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.CharField(default=UserRole.PLAYER)

    class Meta:
        model = User
        fields = ('email', 'password', 'nickname', 'role')

    def validate_email(self, value):
        # Cyrillic Excluding
        if contains_cyrillic(value):
            raise serializers.ValidationError('Електронна адреса не повинна містити кирилиці.')
        
        value = value.strip().lower()
        # Django Validation
        django_validate_email(value)

        # Check - Email Domain
        domain = value.split('@')[-1]
        if domain not in settings.ALLOWED_EMAIL_DOMAINS:
            raise serializers.ValidationError(
                'Дозволені лише email на: gmail.com, outlook.com, hotmail.com, live.com, yahoo.com, icloud.com, ukr.net'
            )

        # Check - Every email must be unique
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Користувач з таким email вже існує.')

        # Super Check
        try:
            validate_email(value, check_deliverability=True)
        except EmailNotValidError:
            raise serializers.ValidationError('Електронна адреса недійсна.')

        return value

    def validate_role(self, value):
        if value == TEAM_ROLE_ALIAS:
            return UserRole.CAPTAIN
        if value not in UserRole.values:
            raise serializers.ValidationError('Некоректна роль.')
        return value

    def validate_password(self, value):
        return validate_password_complexity(value)

    def create(self, validated_data):
        password = validated_data.pop('password')
        return User.objects.create_user(password=password, **validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email', '').lower()
        password = attrs.get('password')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError('Користувача не знайдено') from exc
        if not user.check_password(password):
            raise serializers.ValidationError('Невірний пароль')
        attrs['user'] = user
        return attrs

    def to_representation(self, instance):
        user = instance['user']
        return {
            'access_token': create_access_token(user),
            'role': user.role,
            'nickname': user.nickname,
            'user_id': user.id,
            'email': user.email,
        }


class TournamentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = ('id', 'title', 'description', 'reg_start', 'reg_end', 'max_teams')

    def validate(self, attrs):
        reg_start = attrs.get('reg_start')
        reg_end = attrs.get('reg_end')
        if reg_start and reg_end and reg_end <= reg_start:
            raise serializers.ValidationError('Дата завершення реєстрації має бути пізніше за дату початку.')
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        return Tournament.objects.create(creator=request.user, status=TournamentStatus.DRAFT, **validated_data)


class TournamentOutSerializer(serializers.ModelSerializer):
    creator_id = serializers.IntegerField(source='creator.id', read_only=True)
    cover_image_path = serializers.SerializerMethodField()
    teams_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tournament
        fields = ('id', 'title', 'description', 'status', 'creator_id', 'reg_start', 'reg_end', 'max_teams', 'cover_image_path', 'teams_count')

    def get_cover_image_path(self, obj):
        return obj.cover_image.url if obj.cover_image else None


class TeamMemberCreateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()


class TeamOutSerializer(serializers.ModelSerializer):
    image_path = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ('id', 'name', 'tournament_id', 'captain_email', 'captain_name', 'image_path')

    def get_image_path(self, obj):
        return obj.image.url if obj.image else None


class TeamCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    tournament_id = serializers.IntegerField()
    captain_email = serializers.EmailField()
    captain_name = serializers.CharField(max_length=255)
    members = TeamMemberCreateSerializer(many=True, required=False, default=list)

    def validate(self, attrs):
        try:
            tournament = Tournament.objects.get(pk=attrs['tournament_id'])
        except Tournament.DoesNotExist as exc:
            raise serializers.ValidationError('Турнір не знайдено') from exc

        if tournament.status != TournamentStatus.REGISTRATION:
            raise serializers.ValidationError('Реєстрація на цей турнір закрита або ще не почалася')

        now = timezone.now()
        if tournament.reg_start and tournament.reg_end and not (tournament.reg_start <= now <= tournament.reg_end):
            raise serializers.ValidationError('Ви поза межами реєстраційного вікна')

        current_teams_count = Team.objects.filter(tournament=tournament).count()
        if tournament.max_teams and current_teams_count >= tournament.max_teams:
            raise serializers.ValidationError(f'Усі місця на турнір зайняті (макс. {tournament.max_teams})')

        members = attrs.get('members', [])
        max_members = 5
        if len(members) > max_members:
            raise serializers.ValidationError(f'Максимальна кількість учасників — {max_members}')

        all_emails = [attrs['captain_email'].lower()] + [member['email'].lower() for member in members]
        duplicates = [email for email, count in Counter(all_emails).items() if count > 1]
        if duplicates:
            raise serializers.ValidationError('Один і той самий email вказано кілька разів')

        for email in all_emails:
            exists_as_captain = Team.objects.filter(tournament=tournament, captain_email=email).exists()
            exists_as_member = TeamMember.objects.filter(team__tournament=tournament, email=email).exists()
            if exists_as_captain or exists_as_member:
                raise serializers.ValidationError(f'Учасник з email {email} вже зареєстрований у цьому турнірі')

        attrs['tournament'] = tournament
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        members_data = validated_data.pop('members', [])
        tournament = validated_data.pop('tournament')
        team = Team.objects.create(
            tournament=tournament,
            captain=self.context['request'].user if self.context['request'].user.is_authenticated else None,
            **validated_data,
        )
        TeamMember.objects.bulk_create([
            TeamMember(team=team, **member) for member in members_data
        ])
        return team


class RoundCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Round
        fields = ('id', 'title', 'description', 'requirements', 'evaluation_criteria', 'start_time', 'end_time', 'tournament')

    def validate(self, attrs):
        if attrs['end_time'] <= attrs['start_time']:
            raise serializers.ValidationError('Час завершення має бути пізніше за час початку')
        return attrs


class SubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ('id', 'team', 'round', 'github_link', 'video_link', 'description')

    def validate(self, attrs):
        round_obj = attrs['round']
        if round_obj.end_time < timezone.now():
            raise serializers.ValidationError('Час подачі робіт вичерпано або раунд не знайдено')
        return attrs


class EvaluationOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluation
        fields = ('id', 'submission_id', 'jury_id', 'tech_score', 'func_score', 'created_at')


class LeaderboardEntrySerializer(serializers.Serializer):
    team_name = serializers.CharField()
    total_score = serializers.FloatField()
    tech_avg = serializers.FloatField()
    func_avg = serializers.FloatField()
    submissions_count = serializers.IntegerField()
