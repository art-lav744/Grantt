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
    role = serializers.CharField(required=False, default=UserRole.PARTICIPANT)

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
        if value in (None, ''):
            return UserRole.PARTICIPANT
        if value != UserRole.PARTICIPANT:
            raise serializers.ValidationError('Самостійно обрати роль при реєстрації не можна.')
        return value

    def validate_password(self, value):
        return validate_password_complexity(value)

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data['role'] = UserRole.PARTICIPANT
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
        fields = '__all__'

    def validate(self, data):
        # Перевірка логічного ланцюжка часу
        if data['reg_end'] <= data['reg_start']:
            raise serializers.ValidationError("Реєстрація не може закінчитися раніше, ніж почнеться.")
        
        # Ви просили, щоб початок турніру збігався з кінцем реєстрації
        if data['start_time'] < data['reg_end']:
            raise serializers.ValidationError("Турнір не може початися раніше завершення реєстрації.")
            
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError("Турнір не може завершитися раніше, ніж почнеться.")
            
        return data


class TournamentOutSerializer(serializers.ModelSerializer):
    creator_id = serializers.IntegerField(source='creator.id', read_only=True)
    cover_image_path = serializers.SerializerMethodField()
    teams_count = serializers.IntegerField(read_only=True)
    logical_status = serializers.ReadOnlyField()
    
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
#existence
        try:
            tournament = Tournament.objects.get(pk=attrs['tournament_id'])
        except Tournament.DoesNotExist as exc:
            raise serializers.ValidationError('Турнір не знайдено') from exc
#status
        if tournament.status != TournamentStatus.REGISTRATION:
            raise serializers.ValidationError('Реєстрація на цей турнір закрита або ще не почалася')
#time
        now = timezone.now()
        if tournament.reg_start and tournament.reg_end and not (tournament.reg_start <= now <= tournament.reg_end):
            raise serializers.ValidationError('Ви поза межами реєстраційного вікна')
#enough room
        current_teams_count = Team.objects.filter(tournament=tournament).count()
        if tournament.max_teams and current_teams_count >= tournament.max_teams:
            raise serializers.ValidationError(f'Усі місця на турнір зайняті (макс. {tournament.max_teams})')
#captain email check
        captain_email = attrs['captain_email'].lower()
        if Team.objects.filter(tournament=tournament, captain_email=captain_email).exists():
            raise serializers.ValidationError('Капітан з таким email вже має команду на цей турнір.')
# Перевірка по User об'єкту для автентифікованих користувачів
        if self.context.get('request') and self.context['request'].user.is_authenticated:
            if Team.objects.filter(tournament=tournament, captain=self.context['request'].user).exists():
                raise serializers.ValidationError('Ви вже маєте команду на цей турнір.')
#members email check
        members = attrs.get('members', [])
        total_people = len(members) + 1  # капітан + члени
        if total_people > tournament.max_team_members or total_people < tournament.min_team_members:
            raise serializers.ValidationError(f'Кількість учасників не відповідає вимогам (від {tournament.min_team_members} до {tournament.max_team_members}), зараз: {total_people}')
#members count
        all_emails = [captain_email] + [member['email'].lower() for member in members]
        duplicates = [email for email, count in Counter(all_emails).items() if count > 1]
        if duplicates:
            raise serializers.ValidationError('Один і той самий email вказано кілька разів')
#already registered
        existing_as_captain = Team.objects.filter(tournament=tournament, captain_email__in=all_emails).values_list('captain_email', flat=True)
        existing_as_member = TeamMember.objects.filter(team__tournament=tournament, email__in=all_emails).values_list('email', flat=True)
        already_registered = set(existing_as_captain) | set(existing_as_member)

        if already_registered:
            raise serializers.ValidationError(f'Учасники з email {", ".join(already_registered)} вже зареєстровані у цьому турнірі')

        attrs['tournament'] = tournament
        attrs.pop('tournament_id', None)
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        members_data = validated_data.pop('members', [])
        tournament = validated_data.pop('tournament')
        validated_data['captain_email'] = validated_data['captain_email'].lower()
        team = Team.objects.create(
            tournament=tournament,
            captain=self.context['request'].user if self.context['request'].user.is_authenticated else None,
            **validated_data,
        )
        TeamMember.objects.bulk_create([
            TeamMember(team=team, email=member['email'].lower(), full_name=member['full_name']) 
            for member in members_data
        ])
        return team


class RoundCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Round
        fields = ('id', 'title', 'description', 'requirements', 'start_time', 'end_time', 'tournament')

    def validate(self, attrs):
        if attrs['end_time'] <= attrs['start_time']:
            raise serializers.ValidationError('Час завершення має бути пізніше за час початку')
        return attrs


class SubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ('id', 'team', 'round', 'github_link', 'video_link', 'description', 'created_at')

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
