from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError

from .models import User, Submission, UserRole

from email_validator import EmailNotValidError, validate_email

class RegisterForm(UserCreationForm):
    email = forms.EmailField(label="Email")
    nickname = forms.CharField(label="Нікнейм", max_length=150)
    role = forms.ChoiceField(
        label="Роль",
        choices=UserRole.choices,
        initial=UserRole.TEAM,
    )

    class Meta:
        model = User
        fields = ("email", "nickname", "role", "password1", "password2")

    def clean_email(self):
        raw_email = self.cleaned_data["email"].strip().lower()

        try:
            validated = validate_email(
                raw_email,
                check_deliverability=True,
            )
            email = validated.normalized
        except EmailNotValidError as exc:
            raise ValidationError(str(exc))

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Користувач з таким email вже існує.")

        return email

    def clean_nickname(self):
        nickname = self.cleaned_data["nickname"].strip()
        if User.objects.filter(nickname__iexact=nickname).exists():
            raise ValidationError("Користувач з таким нікнеймом вже існує.")
        return nickname

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.nickname = self.cleaned_data["nickname"]
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ["round", "github_link", "video_link", "description"]
        labels = {
            "round": "Раунд",
            "github_link": "GitHub посилання",
            "video_link": "Відео посилання",
            "description": "Опис",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        team = kwargs.pop("team", None)
        super().__init__(*args, **kwargs)

        if team is not None and getattr(team, "tournament", None) is not None:
            self.fields["round"].queryset = self.fields["round"].queryset.filter(
                tournament=team.tournament
            ).order_by("start_time", "id")
