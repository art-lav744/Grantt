import re

from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Submission, TeamMember, Tournament, User, UserRole, Round, Team


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label='Email')
    nickname = forms.CharField(label='Нікнейм', max_length=150)

    class Meta:
        model = User
        fields = ('email', 'nickname', 'full_name', 'password1', 'password2')

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
            error_list = []
            if len(password) < 8:
                error_list.append('Пароль має містити щонайменше 8 символів.')
            if not re.search(r'[A-Z]', password):
                error_list.append('Додайте хоча б одну велику літеру.')
            if not re.search(r'[a-z]', password):
                error_list.append('Додайте хоча б одну малу літеру.')
            if not re.search(r'[0-9]', password):
                error_list.append('Додайте хоча б одну цифру.')
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                error_list.append('Додайте хоча б один спеціальний символ.')

            if error_list:
                raise ValidationError(error_list)

        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.nickname = self.cleaned_data['nickname']
        user.role = UserRole.PARTICIPANT
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

User=get_user_model()
class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['nickname', 'full_name', 'discord_tag', 'profile_image']
        labels = {
            'nickname': 'Нікнейм',
            'full_name': 'ПІБ',
            'discord_tag': 'Discord тег',
            'profile_image': 'Аватарка',
        }
        widgets = {
            'nickname': forms.TextInput(attrs={'placeholder': 'Ваш нікнейм'}),
            'full_name': forms.TextInput(attrs={'placeholder': 'Прізвище Ім\'я По-батькові'}),
            'discord_tag': forms.TextInput(attrs={'placeholder': 'username#0000 або @username'}),
        }
 
    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname')
        qs = User.objects.filter(nickname=nickname).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Цей нікнейм вже зайнятий.')
        return nickname
 

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name']  # Додайте інші поля моделі Team, якщо вони є
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Назва вашої команди'}),
        }

class RoundForm(forms.ModelForm):
    class Meta:
        model = Round
        fields = ['title', 'description', 'requirements', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'requirements': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
        }

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

class AddMemberForm(forms.Form):
    email = forms.EmailField(label="Email учасника")

    def __init__(self, *args, **kwargs):
        self.team = kwargs.pop('team')
        self.request_user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email').lower().strip()
        
        # 1. Перевірка, чи не намагається капітан додати самого себе
        if email == self.request_user.email.lower():
            raise ValidationError("Ви вже є капітаном цієї команди. Себе додавати не потрібно.")

        # Отримуємо об'єкт користувача, якого хочуть додати
        user_to_add = User.objects.filter(email__iexact=email).first()
        if not user_to_add:
            raise ValidationError("Користувача з таким email не знайдено.")

        # 2. Перевірка: чи цей користувач вже є в ЯКІЙСЬ команді ЦЬОГО турніру?
        tournament = self.team.tournament
        
        # Перевірка серед капітанів турніру
        is_captain_in_tournament = Team.objects.filter(
            tournament=tournament, 
            captain=user_to_add
        ).exists()
        
        # Перевірка серед учасників турніру
        is_member_in_tournament = TeamMember.objects.filter(
            team__tournament=tournament, 
            user=user_to_add
        ).exists()

        if is_captain_in_tournament or is_member_in_tournament:
            raise ValidationError("Цей користувач вже зареєстрований у складі іншої команди на цей турнір.")
            
        return email

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