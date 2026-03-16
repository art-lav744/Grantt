import io
import re
import uuid
from datetime import datetime, timezone as dt_timezone

import jwt
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image
from rest_framework import exceptions

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import Tournament, Team, TeamMember, Round, Submission

def home(request):
    return render(request, "home.html")

def tournament_list(request):
    tournaments = Tournament.objects.all()
    return render(request, "tournaments/tournament_list.html", {
        "tournaments": tournaments
    })

def tournament_detail(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    teams = Team.objects.filter(tournament=tournament)
    rounds = Round.objects.filter(tournament=tournament)
    return render(request, "tournaments/tournament_detail.html", {
        "tournament": tournament,
        "teams": teams,
        "rounds": rounds,
    })

@login_required
def dashboard(request):
    teams = Team.objects.filter(owner=request.user)
    return render(request, "tournaments/dashboard.html", {
        "teams": teams
    })

@login_required
def team_detail(request, pk):
    team = get_object_or_404(Team, pk=pk)
    members = TeamMember.objects.filter(team=team)
    submissions = Submission.objects.filter(team=team)
    return render(request, "tournaments/team_detail.html", {
        "team": team,
        "members": members,
        "submissions": submissions,
    })

ALLOWED_CONTENT_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
MAX_FILE_SIZE_MB = 5
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_NUMBER = True
PASSWORD_REQUIRE_SPECIAL = True


def contains_cyrillic(value: str) -> bool:
    return bool(re.search(r'[Ѐ-ӿ]', value or ''))


def validate_password_complexity(value: str) -> str:
    if len(value) < PASSWORD_MIN_LENGTH:
        raise exceptions.ValidationError(f'Пароль має бути не менше {PASSWORD_MIN_LENGTH} символів')
    if PASSWORD_REQUIRE_NUMBER and not any(ch.isdigit() for ch in value):
        raise exceptions.ValidationError('Пароль має містити хоча б одну цифру')
    if PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise exceptions.ValidationError('Пароль має містити хоча б один спеціальний символ')
    return value


def create_access_token(user):
    payload = {
        'sub': str(user.pk),
        'role': user.role,
        'exp': datetime.now(dt_timezone.utc) + settings.JWT_ACCESS_LIFETIME,
        'email': user.email,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise exceptions.AuthenticationFailed('Invalid token') from exc


def process_square_image(uploaded_file, target_size=400):
    uploaded_file.seek(0)
    content_type = getattr(uploaded_file, 'content_type', None)
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise exceptions.ValidationError(f"Invalid file type '{content_type}'.")
    size_mb = uploaded_file.size / (1024 * 1024)
    if uploaded_file.size == 0:
        raise exceptions.ValidationError('File is empty.')
    if size_mb > MAX_FILE_SIZE_MB:
        raise exceptions.ValidationError(f'File too large ({size_mb:.1f} MB). Max {MAX_FILE_SIZE_MB} MB.')
    try:
        image = Image.open(uploaded_file)
    except Exception as exc:
        raise exceptions.ValidationError('File is corrupted or not a valid image.') from exc
    if image.mode in ('RGBA', 'P'):
        image = image.convert('RGB')
    w, h = image.size
    min_side = min(w, h)
    left = (w - min_side) // 2
    top = (h - min_side) // 2
    image = image.crop((left, top, left + min_side, top + min_side))
    image = image.resize((target_size, target_size), Image.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=85)
    return ContentFile(buffer.getvalue(), name=f'{uuid.uuid4().hex}.jpg')


def validate_raw_image(uploaded_file):
    uploaded_file.seek(0)
    content_type = getattr(uploaded_file, 'content_type', None)
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise exceptions.ValidationError(f"Invalid file type '{content_type}'.")
    size_mb = uploaded_file.size / (1024 * 1024)
    if uploaded_file.size == 0:
        raise exceptions.ValidationError('File is empty.')
    if size_mb > MAX_FILE_SIZE_MB:
        raise exceptions.ValidationError(f'File too large ({size_mb:.1f} MB). Max {MAX_FILE_SIZE_MB} MB.')
    try:
        image = Image.open(uploaded_file)
        image.verify()
    except Exception as exc:
        raise exceptions.ValidationError('File is corrupted or not a valid image.') from exc
    uploaded_file.seek(0)
    ext = uploaded_file.name.rsplit('.', 1)[-1].lower() if '.' in uploaded_file.name else 'jpg'
    return ContentFile(uploaded_file.read(), name=f'{uuid.uuid4().hex}.{ext}')
