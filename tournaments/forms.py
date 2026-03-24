import re

from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import Submission, TeamMember, Tournament, User, UserRole


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label='Email')
    nickname = forms.CharField(label='Нікнейм', max_length=150)
    role = forms.ChoiceField(
        label='Хто ви?',
        choices=[
            (UserRole.CAPTAIN, 'Капітан команди (створює команду)'),
            (UserRole.PLAYER, 'Учасник (доєднується до команди)'),
        ],
        initial=UserRole.PLAYER,
    )

    class Meta:
        model = User
        fields = ('email', 'nickname', 'role', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = (
            'Мінімум 8 символів: велика та мала літери, цифра і спецсимвол (!@#$%^&*).'
        )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        domain = email.split('@')[-1]

        if domain not in settings.ALLOWED_EMAIL_DOMAINS:
            raise ValidationError(
                'Дозволені лише email на: gmail.com, outlook.com, hotmail.com, '
                'live.com, yahoo.com, icloud.com, ukr.net'
            )

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Користувач з таким email вже існує.')
        return email

    def clean_nickname(self):
        nickname = self.cleaned_data['nickname'].strip()
        if User.objects.filter(nickname__iexact=nickname).exists():
            raise ValidationError('Користувач з таким нікнеймом вже існує.')
        return nickname

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password:
            if len(password) < 8:
                raise ValidationError('Пароль має містити щонайменше 8 символів.')
            if not re.search(r'[A-Z]', password):
                raise ValidationError('Додайте хоча б одну велику літеру.')
            if not re.search(r'[a-z]', password):
                raise ValidationError('Додайте хоча б одну малу літеру.')
            if not re.search(r'[0-9]', password):
                raise ValidationError('Додайте хоча б одну цифру.')
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                raise ValidationError('Додайте хоча б один спеціальний символ.')
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.nickname = self.cleaned_data['nickname']
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_verified:
            raise forms.ValidationError('Спочатку підтвердіть email.')


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['round', 'github_link', 'video_link', 'description']
        labels = {
            'round': 'Раунд',
            'github_link': 'GitHub посилання',
            'video_link': 'Відео посилання',
            'description': 'Опис',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        team = kwargs.pop('team', None)
        super().__init__(*args, **kwargs)

        if team is not None and getattr(team, 'tournament', None) is not None:
            self.fields['round'].queryset = self.fields['round'].queryset.filter(
                tournament=team.tournament
            ).order_by('start_time', 'id')


class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = ['full_name', 'email']
        labels = {
            'full_name': 'ПІБ учасника',
            'email': 'Email учасника',
        }

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()


class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = ['title', 'description', 'reg_start', 'reg_end', 'start_time', 'end_time', 'max_teams', 'cover_image']
        widgets = {
            'reg_start': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}, format='%Y-%m-%dT%H:%M'),
            'reg_end': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}, format='%Y-%m-%dT%H:%M'),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}, format='%Y-%m-%dT%H:%M'),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Примусове форматування для коректного відображення при редагуванні
        date_fields = ['reg_start', 'reg_end', 'start_time', 'end_time']
        for field in date_fields:
            if self.instance and getattr(self.instance, field):
                self.initial[field] = getattr(self.instance, field).strftime('%Y-%m-%dT%H:%M')

    def clean(self):
        cd = super().clean()
        # Логічна перевірка ланцюжка дат
        if cd.get('reg_end') <= cd.get('reg_start'):
            self.add_error('reg_end', "Реєстрація не може закінчитися раніше початку")
        if cd.get('start_time') < cd.get('reg_start'):
            self.add_error('start_time', "Турнір не може початися раніше реєстрації")
        if cd.get('end_time') <= cd.get('start_time'):
            self.add_error('end_time', "Турнір не може закінчитися раніше свого початку")
        return cd