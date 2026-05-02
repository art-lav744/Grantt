from collections import Counter

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.core.validators import validate_email as django_validate_email
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import serializers

from email_validator import EmailNotValidError, validate_email

from .models import Evaluation, JuryTournamentRegistration, Round, Submission, SubmissionStatus, Team, TeamMember, Tournament, TournamentFile, TournamentStatus, User, UserRole
from .utils import (
    contains_cyrillic,
    create_access_token,
    normalize_email_value,
    tournament_registration_error,
    validate_allowed_email_domain,
    validate_password_complexity,
)



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
        
        value = normalize_email_value(value)
        # Django Validation
        django_validate_email(value)

        # Check - Email Domain
        try:
            validate_allowed_email_domain(value)
        except ValueError as exc:
            raise serializers.ValidationError(exc.args[0])

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
        try:
            return validate_password_complexity(value)
        except ValueError as exc:
            raise serializers.ValidationError(exc.args[0])

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
        if data.get('max_rounds', 1) < 1:
            raise serializers.ValidationError({'max_rounds': 'Має бути щонайменше 1 раунд.'})

        return data


class TournamentOutSerializer(serializers.ModelSerializer):
    creator_id = serializers.IntegerField(source='creator.id', read_only=True)
    cover_image_path = serializers.SerializerMethodField()
    teams_count = serializers.IntegerField(read_only=True)
    logical_status = serializers.ReadOnlyField()
    
    class Meta:
        model = Tournament
        fields = ('id', 'title', 'description', 'status', 'logical_status', 'creator_id', 'reg_start', 'reg_end', 'max_teams', 'max_rounds', 'max_team_members', 'min_team_members', 'hide_teams_until_registration_end', 'cover_image_path', 'teams_count')

    def get_cover_image_path(self, obj):
        return obj.cover_image.url if obj.cover_image else None


class TeamMemberCreateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()

class TeamMemberOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = ('id', 'full_name', 'email', 'user_id')


class TeamOutSerializer(serializers.ModelSerializer):
    image_path = serializers.SerializerMethodField()
    members_count = serializers.IntegerField(read_only=True)
    members = TeamMemberOutSerializer(source='memberships', many=True, read_only=True)

    class Meta:
        model = Team
        fields = ('id', 'name', 'tournament_id', 'captain_email', 'captain_name', 'members_count', 'members', 'image_path')

    def get_image_path(self, obj):
        image = getattr(obj, 'image', None)
        return image.url if image else None


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
        now = timezone.now()
        registration_error = tournament_registration_error(tournament, now=now)
        if registration_error:
            raise serializers.ValidationError(registration_error)
#enough room
        current_teams_count = Team.objects.filter(tournament=tournament).count()
        if tournament.max_teams and current_teams_count >= tournament.max_teams:
            raise serializers.ValidationError(f'Усі місця на турнір зайняті (макс. {tournament.max_teams})')
#captain email check
        captain_email = normalize_email_value(attrs['captain_email'])
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
        all_emails = [captain_email] + [normalize_email_value(member['email']) for member in members]
        duplicates = [email for email, count in Counter(all_emails).items() if count > 1]
        if duplicates:
            raise serializers.ValidationError('Один і той самий email вказано кілька разів')
#already registered
        existing_as_captain = Team.objects.filter(tournament=tournament, captain_email__in=all_emails).values_list('captain_email', flat=True)
        existing_as_member = TeamMember.objects.filter(team__tournament=tournament, email__in=all_emails).values_list('email', flat=True)
        already_registered = set(existing_as_captain) | set(existing_as_member)

        if already_registered:
            raise serializers.ValidationError(f'Учасники з email {", ".join(already_registered)} вже зареєстровані у цьому турнірі')

        user_ids = list(User.objects.filter(email__in=all_emails).values_list('id', flat=True))
        if user_ids and TeamMember.objects.filter(team__tournament=tournament, user_id__in=user_ids).exists():
            raise serializers.ValidationError('Один з користувачів вже є учасником команди у цьому турнірі.')

        attrs['tournament'] = tournament
        attrs.pop('tournament_id', None)
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        members_data = validated_data.pop('members', [])
        tournament = validated_data.pop('tournament')
        validated_data['captain_email'] = normalize_email_value(validated_data['captain_email'])
        team = Team.objects.create(
            tournament=tournament,
            captain=self.context['request'].user if self.context['request'].user.is_authenticated else None,
            **validated_data,
        )
        for member in members_data:
            email = normalize_email_value(member['email'])
            linked_user = User.objects.filter(email__iexact=email).first()
            TeamMember.objects.create(
                team=team,
                email=email,
                full_name=member['full_name'],
                user=linked_user,
            )
        return team


class RoundCreateSerializer(serializers.ModelSerializer):
    criteria = serializers.ListField(child=serializers.DictField(), write_only=True, required=False)
    criteria_definition = serializers.CharField(write_only=True, required=False, allow_blank=False)

    class Meta:
        model = Round
        fields = ('id', 'title', 'description', 'requirements', 'evaluation_criteria', 'criteria', 'criteria_definition', 'start_time', 'end_time', 'status', 'tournament')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        criteria = instance.get_or_create_scoring_criteria()
        data['criteria'] = [
            {'id': criterion.id, 'name': criterion.name, 'max_score': criterion.max_score, 'order': criterion.order}
            for criterion in criteria
        ]
        data['evaluation_criteria'] = instance.format_criteria_definition([
            {'name': criterion.name, 'max_score': criterion.max_score}
            for criterion in criteria
        ])
        return data

    def validate(self, attrs):
        start_time = attrs.get('start_time', getattr(self.instance, 'start_time', None))
        end_time = attrs.get('end_time', getattr(self.instance, 'end_time', None))
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError('Час завершення має бути пізніше за час початку')

        tournament = attrs.get('tournament', getattr(self.instance, 'tournament', None))
        if self.instance is None and tournament and tournament.max_rounds and tournament.rounds.count() >= tournament.max_rounds:
            raise serializers.ValidationError({'tournament': f'Досягнуто ліміту раундів для цього турніру ({tournament.max_rounds}).'})

        raw_criteria = attrs.get('criteria')
        if raw_criteria is None:
            raw_criteria = attrs.get('criteria_definition', attrs.get('evaluation_criteria'))
        if raw_criteria is not None or self.instance is None:
            try:
                attrs['parsed_criteria'] = Round.validate_criteria_payload(
                    Round.parse_criteria_definition(raw_criteria or list(Round.DEFAULT_CRITERIA))
                )
            except ValidationError as exc:
                raise serializers.ValidationError({'criteria': exc.messages})
        return attrs

    def create(self, validated_data):
        parsed_criteria = validated_data.pop('parsed_criteria')
        validated_data.pop('criteria', None)
        validated_data.pop('criteria_definition', None)
        validated_data['evaluation_criteria'] = Round.format_criteria_definition(parsed_criteria)
        round_obj = super().create(validated_data)
        round_obj.set_scoring_criteria(parsed_criteria)
        return round_obj

    def update(self, instance, validated_data):
        parsed_criteria = validated_data.pop('parsed_criteria', None)
        validated_data.pop('criteria', None)
        validated_data.pop('criteria_definition', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if parsed_criteria is not None:
            instance.set_scoring_criteria(parsed_criteria)
        return instance


class SubmissionCreateSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = ('id', 'team', 'round', 'github_link', 'video_link', 'description', 'status', 'created_at')

    def get_status(self, obj):
        return obj.status

    def validate(self, attrs):
        round_obj = attrs['round']
        team = attrs['team']
        if team.tournament_id != round_obj.tournament_id:
            raise serializers.ValidationError('Команда і раунд мають належати одному турніру.')
        if not round_obj.accepts_submissions():
            raise serializers.ValidationError('Подання або оновлення відповіді для цього раунду вже недоступне')
        return attrs

    def create(self, validated_data):
        submission, _ = Submission.objects.update_or_create(
            team=validated_data['team'],
            round=validated_data['round'],
            defaults={
                'github_link': validated_data['github_link'],
                'video_link': validated_data['video_link'],
                'description': validated_data['description'],
            },
        )
        return submission


class EvaluationOutSerializer(serializers.ModelSerializer):
    criteria_scores = serializers.SerializerMethodField()
    total_score = serializers.SerializerMethodField()
    total_percentage = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    team_name = serializers.CharField(source='submission.team.name', read_only=True)
    round_title = serializers.CharField(source='submission.round.title', read_only=True)
    tournament_id = serializers.IntegerField(source='submission.round.tournament_id', read_only=True)

    class Meta:
        model = Evaluation
        fields = ('id', 'submission_id', 'jury_id', 'team_name', 'round_title', 'tournament_id', 'status', 'criteria_scores', 'total_score', 'total_percentage', 'created_at')

    def get_status(self, obj):
        return SubmissionStatus.EVALUATED if obj.is_scored() else SubmissionStatus.PENDING

    def get_criteria_scores(self, obj):
        scores = obj.ensure_score_entries()
        return [
            {
                'criterion_id': item.criterion_id,
                'name': item.criterion.name,
                'max_score': item.criterion.max_score,
                'score': item.score,
            }
            for item in scores
        ]

    def get_total_score(self, obj):
        return obj.total_score()

    def get_total_percentage(self, obj):
        max_total = obj.submission.round.total_max_score()
        return (obj.total_score() / max_total * 100) if max_total else 0.0


class LeaderboardEntrySerializer(serializers.Serializer):
    team_name = serializers.CharField()
    total_score = serializers.FloatField()
    average_score = serializers.FloatField()
    criteria_summary = serializers.ListField()
    submissions_count = serializers.IntegerField()



class TournamentFileOutSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = TournamentFile
        fields = ('id', 'tournament_id', 'title', 'file_type', 'file_url', 'uploaded_by_name', 'uploaded_at')

    def get_file_url(self, obj):
        request = self.context.get('request')
        if not obj.file:
            return None
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url

    def get_uploaded_by_name(self, obj):
        if not obj.uploaded_by:
            return None
        return obj.uploaded_by.full_name or obj.uploaded_by.nickname or obj.uploaded_by.email


class JuryTournamentRegistrationOutSerializer(serializers.ModelSerializer):
    jury_email = serializers.EmailField(source='jury.email', read_only=True)
    jury_nickname = serializers.CharField(source='jury.nickname', read_only=True)
    tournament_title = serializers.CharField(source='tournament.title', read_only=True)
    reviewed_by_email = serializers.EmailField(source='reviewed_by.email', read_only=True, allow_null=True)

    class Meta:
        model = JuryTournamentRegistration
        fields = (
            'id',
            'jury',
            'jury_email',
            'jury_nickname',
            'tournament',
            'tournament_title',
            'status',
            'reviewed_by',
            'reviewed_by_email',
            'reviewed_at',
            'created_at',
            'updated_at',
        )
