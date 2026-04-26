import io
import re
import uuid
from datetime import datetime, timezone as dt_timezone

import jwt
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from PIL import Image
from rest_framework import exceptions


ALLOWED_CONTENT_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
MAX_FILE_SIZE_MB = 5
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_NUMBER = True
PASSWORD_REQUIRE_SPECIAL = True


TOURNAMENT_MANUAL_STATUSES = {'draft', 'registration', 'open', 'closed', 'archived'}
TOURNAMENT_LOGICAL_STATUS_LABELS = {
    'draft': 'Draft',
    'registration': 'Registration',
    'open': 'Running',
    'closed': 'Finished',
    'archived': 'Archived',
    'scheduled': 'Scheduled',
    'finished': 'Finished',
}


def contains_cyrillic(value: str) -> bool:
    return bool(re.search(r'[Ѐ-ӿ]', value or ''))



def normalize_email_value(value: str) -> str:
    return (value or '').strip().lower()



def validate_allowed_email_domain(value: str) -> str:
    email = normalize_email_value(value)
    domain = email.split('@')[-1]
    if domain not in settings.ALLOWED_EMAIL_DOMAINS:
        raise ValueError(
            'Дозволені лише email на: gmail.com, outlook.com, hotmail.com, '
            'live.com, yahoo.com, icloud.com, ukr.net'
        )
    return email



def validate_password_complexity(value: str) -> str:
    error_list = []

    if len(value) < PASSWORD_MIN_LENGTH:
        error_list.append(f'Пароль має бути не менше {PASSWORD_MIN_LENGTH} символів')
    if PASSWORD_REQUIRE_NUMBER and not any(ch.isdigit() for ch in value):
        error_list.append('Пароль має містити хоча б одну цифру')
    if PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        error_list.append('Пароль має містити хоча б один спеціальний символ')

    if error_list:
        raise ValueError(error_list)

    return value



def get_tournament_logical_status(tournament, now=None) -> str:
    now = now or timezone.now()

    if tournament.status == 'draft':
        return TOURNAMENT_LOGICAL_STATUS_LABELS['draft']
    if tournament.status == 'archived':
        return TOURNAMENT_LOGICAL_STATUS_LABELS['archived']
    if tournament.status == 'closed':
        return TOURNAMENT_LOGICAL_STATUS_LABELS['closed']

    if now < tournament.reg_start:
        return TOURNAMENT_LOGICAL_STATUS_LABELS['scheduled']
    if tournament.reg_start <= now <= tournament.reg_end and tournament.status == 'registration':
        return TOURNAMENT_LOGICAL_STATUS_LABELS['registration']
    if tournament.start_time <= now <= tournament.end_time and tournament.status in {'registration', 'open'}:
        return TOURNAMENT_LOGICAL_STATUS_LABELS['open']
    if now > tournament.end_time:
        return TOURNAMENT_LOGICAL_STATUS_LABELS['finished']

    return TOURNAMENT_LOGICAL_STATUS_LABELS.get(tournament.status, tournament.status)


<<<<<<< Updated upstream

=======
>>>>>>> Stashed changes
def tournament_registration_error(tournament, now=None):
    now = now or timezone.now()
    if tournament.status != 'registration':
        return 'Реєстрація на цей турнір закрита або ще не почалася.'
    if not (tournament.reg_start <= now <= tournament.reg_end):
        return 'Реєстрація на цей турнір поза межами реєстраційного вікна.'
    return None



def tournament_registration_is_open(tournament, now=None) -> bool:
    return tournament_registration_error(tournament, now=now) is None



def get_submission_score_summary(submission):
    score_data = submission.calculate_final_score()
    return {
        'criteria': [
            {
                'id': item['id'],
                'name': item['name'],
                'max_score': item['max_score'],
                'average': round(item['average'], 1),
            }
            for item in score_data['criteria']
        ],
        'total_avg': round(score_data['total'], 1) if score_data['total'] is not None else None,
        'raw_total': round(score_data['raw_total'], 1) if score_data['raw_total'] is not None else None,
        'max_total': round(score_data['max_total'], 1) if score_data['max_total'] is not None else None,
        'eval_count': 1 if hasattr(submission, 'evaluation') else 0,
    }



def attach_submission_score_summaries(submissions):
    result = []
    for submission in submissions:
        summary = get_submission_score_summary(submission)
        submission.criteria_summary = summary['criteria']
        submission.criteria_preview = ', '.join(
            f"{item['name']}: {item['average']}/{item['max_score']}"
            for item in summary['criteria']
        )
        submission.total_avg = summary['total_avg']
        submission.raw_total = summary['raw_total']
        submission.max_total = summary['max_total']
        submission.eval_count = summary['eval_count']
        result.append(submission)
    return result



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
