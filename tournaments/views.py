import random
import secrets
import string

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models.functions import TruncDate
from django.db.models import Count
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import AddMemberForm, ProfileEditForm, RegisterForm, RoundForm, SubmissionForm, TournamentFileForm, TournamentForm, JuryAssignmentForm
from .models import Evaluation, JuryRegistrationStatus, JuryTournamentRegistration, Round, RoundStatus, Submission, Team, TeamMember, Tournament, TournamentFile, TournamentStatus, User, UserRole
from .permissions import IsAdmin, IsAuthenticatedJWT, IsJury, IsOrganizerOrAdmin
from .serializers import (
    EvaluationOutSerializer,
    LoginSerializer,
    RegisterSerializer,
    RoundCreateSerializer,
    SubmissionCreateSerializer,
    TeamCreateSerializer,
    TeamOutSerializer,
    TournamentFileOutSerializer,
    TournamentCreateSerializer,
    TournamentOutSerializer,
    UserOutSerializer,
    JuryTournamentRegistrationOutSerializer,
)
from .utils import (
    attach_submission_score_summaries,
    normalize_email_value,
    process_square_image,
    tournament_registration_error,
    validate_raw_image,
)


def _criteria_definition_from_round(round_obj):
    criteria = round_obj.get_or_create_scoring_criteria()
    return Round.format_criteria_definition([
        {'name': criterion.name, 'max_score': criterion.max_score}
        for criterion in criteria
    ])


def home(request):
    now = timezone.now()
    context = {
        'reg_open': Tournament.objects.filter(reg_start__lte=now, reg_end__gte=now),
        'running': Tournament.objects.filter(start_time__lte=now, end_time__gte=now),
        'finished': Tournament.objects.filter(end_time__lt=now),
        'upcoming': Tournament.objects.filter(reg_start__gt=now),
    }
    return render(request, 'home.html', context)



def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_verified = True
        user.save(update_fields=['is_verified'])
        messages.success(request, 'Email підтверджено!')
        return redirect('login')

    messages.error(request, 'Посилання недійсне або застаріле.')
    return redirect('home')



def logout_view(request):
    django_logout(request)
    messages.success(request, 'Ви успішно вийшли з акаунта.')
    return redirect('home')



def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        link = request.build_absolute_uri(f'/verify/{uid}/{token}/')
        send_mail(
            subject='Підтвердіть вашу реєстрацію',
            message=(
                f'Вітаємо, {user.nickname}!\n\n'
                f'Для підтвердження email перейдіть за посиланням:\n{link}\n\n'
                'Посилання дійсне 24 години.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
        messages.success(request, 'На вашу пошту надіслано листа з підтвердженням.')
        return redirect('login')

    return render(request, 'registration/register.html', {'form': form})



def user_management(request):
    if request.user.role == UserRole.ORGANIZER:
        users = User.objects.all()
    elif request.user.role == UserRole.ADMIN:
        users = User.objects.filter(role=UserRole.PARTICIPANT)
    else:
        return redirect('home')
    return render(request, 'management/users.html', {'users': users})



def _get_user_tournament_team(user, tournament):
    if not getattr(user, 'is_authenticated', False):
        return None
    return (
        Team.objects.filter(tournament=tournament, captain=user).first()
        or Team.objects.filter(tournament=tournament, memberships__user=user).distinct().first()
    )



def _get_user_all_teams(user):
    captain_teams = Team.objects.filter(captain=user).select_related('tournament')
    member_teams = Team.objects.filter(memberships__user=user).select_related('tournament').exclude(captain=user)
    return captain_teams, member_teams


def _user_can_access_tournament_files(user, tournament):
    if not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_admin_like', False) or getattr(user, 'is_superuser', False):
        return True
    if _get_user_tournament_team(user, tournament) is None:
        return False
    return tournament.rounds.filter(start_time__lte=timezone.now(), end_time__gte=timezone.now()).exists()


@login_required
def profile_view(request):
    user = request.user
    form = ProfileEditForm(request.POST or None, request.FILES or None, instance=user)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Профіль успішно оновлено!')
            return redirect('profile')
        messages.error(request, 'Будь ласка, виправте помилки у формі.')

    captain_teams, member_teams = _get_user_all_teams(user)
    team_ids = list(captain_teams.values_list('id', flat=True)) + list(member_teams.values_list('id', flat=True))
    submissions = (
        Submission.objects.filter(team__id__in=team_ids)
        .select_related('team', 'round', 'team__tournament', 'evaluation__jury')
        .order_by('-created_at')
    )
    submissions = attach_submission_score_summaries(submissions)
    return render(request, 'tournaments/profile.html', {
        'form': form,
        'captain_teams': captain_teams,
        'member_teams': member_teams,
        'submissions': submissions,
    })


@login_required
def dashboard(request):
    user = request.user
    context = {'role': user.role, 'nickname': user.nickname}

    if user.role == UserRole.ADMIN:
        context['total_users'] = User.objects.count()
        # Додаємо prefetch_related('rounds'), щоб уникнути N+1 запитів у циклі шаблону
        context['tournaments'] = Tournament.objects.all().annotate(
            teams_count=Count('teams')
        ).prefetch_related('rounds') 
        return render(request, 'dashboards/admin_dashboard.html', context)

    if user.role == UserRole.ORGANIZER:
        context['my_tournaments'] = Tournament.objects.filter(creator=user).annotate(teams_count=Count('teams'))
        context['total_users'] = User.objects.count()
        context['tournaments'] = Tournament.objects.all().annotate(teams_count=Count('teams'))
        context['my_evaluations'] = Evaluation.objects.filter(jury=user).select_related('submission__team', 'submission__round')
        return render(request, 'dashboards/organizer_dashboard.html', context)

    if user.role == UserRole.JURY:
        evals = Evaluation.objects.filter(jury=user).select_related('submission__team', 'submission__round').order_by('submission__round__title', 'submission__team__name')
        for evaluation in evals:
            evaluation.criteria_entries = evaluation.ensure_score_entries()
            evaluation.max_total_score = sum(item.criterion.max_score for item in evaluation.criteria_entries)
        total_count = evals.count()
        done_count = sum(1 for e in evals if e.is_scored())
        context.update({
            'my_evaluations': evals,
            'total_count': total_count,
            'done_count': done_count,
            'pending_count': total_count - done_count,
            'assigned_tournaments': user.jury_tournaments.order_by('-created_at', '-id'),
        })
        return render(request, 'dashboards/jury_dashboard.html', context)

    captain_teams, member_teams = _get_user_all_teams(user)
    all_my_teams = (captain_teams | member_teams).distinct()
    context['my_teams'] = all_my_teams
    selected_team_id = request.GET.get('team_id')
    if selected_team_id:
        selected_team = all_my_teams.filter(id=selected_team_id).first()
        if selected_team:
            team_submissions = Submission.objects.filter(team=selected_team).select_related('round').prefetch_related('evaluation').order_by('-created_at')
            context.update({
                'selected_team': selected_team,
                'members': selected_team.memberships.all(),
                'submissions': attach_submission_score_summaries(team_submissions),
                'form': SubmissionForm(team=selected_team),
            })
    return render(request, 'dashboards/team_dashboard.html', context)



def tournament_list(request):
    now = timezone.now()
    tournaments = Tournament.objects.all()

    status = request.GET.get('status')

    if status == 'registration':
        tournaments = tournaments.filter(reg_start__lte=now, reg_end__gte=now)

    elif status == 'running':
        tournaments = tournaments.filter(start_time__lte=now, end_time__gte=now)

    elif status == 'finished':
        tournaments = tournaments.filter(end_time__lt=now)

    elif status == 'upcoming':
        tournaments = tournaments.filter(reg_start__gt=now)

    tournaments = tournaments.order_by('-created_at', '-id')

    return render(request, 'tournaments/tournament_list.html', {
        'tournaments': tournaments,
        'status': status
    })



def tournament_detail(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    teams = tournament.teams.select_related('captain').annotate(members_count=Count('memberships')).prefetch_related('memberships')
    if tournament.hide_teams_until_registration_end and timezone.now() < tournament.reg_end and not (
        getattr(request.user, 'is_authenticated', False) and (request.user.is_superuser or getattr(request.user, 'is_admin_like', False))
    ):
        teams = Team.objects.none()
    rounds = tournament.rounds.order_by('start_time')
    if not (getattr(request.user, 'is_authenticated', False) and (request.user.is_superuser or getattr(request.user, 'is_admin_like', False))):
        rounds = rounds.filter(end_time__lte=timezone.now())
    for round_obj in rounds:
        round_obj.scoring_criteria = round_obj.get_or_create_scoring_criteria()
    user_team = _get_user_tournament_team(request.user, tournament)
    can_access_files = _user_can_access_tournament_files(request.user, tournament)
    return render(request, 'tournaments/tournament_detail.html', {
        'tournament': tournament,
        'teams': teams,
        'rounds': rounds,
        'files': tournament.files.select_related('uploaded_by').all() if can_access_files else [],
        'user_team': user_team,
        'can_access_files': can_access_files,
        'can_manage_rounds': getattr(request.user, 'is_authenticated', False) and (request.user.is_superuser or getattr(request.user, 'is_admin_like', False)),
    })


@login_required
def apply_as_jury(request, tournament_id):
    """Allow jury members to apply for a tournament."""
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    # Only jury members can apply
    if request.user.role not in [UserRole.JURY, UserRole.ORGANIZER]:
        messages.error(request, 'Тільки користувачі з роллю журі можуть подавати заявку.')
        return redirect('tournament_detail', tournament_id=tournament_id)
    
    # Check if already assigned to this tournament
    if tournament in request.user.jury_tournaments.all():
        messages.info(request, 'Ви вже призначені на цей турнір.')
        return redirect('tournament_detail', tournament_id=tournament_id)
    
    # Check if already applied
    existing_registration = JuryTournamentRegistration.objects.filter(
        jury=request.user,
        tournament=tournament
    ).first()
    
    if existing_registration:
        if existing_registration.status == JuryRegistrationStatus.PENDING:
            messages.info(request, 'Ви вже подали заявку на цей турнір (очікує схвалення).')
        elif existing_registration.status == JuryRegistrationStatus.APPROVED:
            messages.info(request, 'Ваша заявка вже схвалена.')
        elif existing_registration.status == JuryRegistrationStatus.REJECTED:
            messages.error(request, 'Ваша попередня заявка була відхилена.')
        return redirect('tournament_detail', tournament_id=tournament_id)
    
    # Create new registration
    JuryTournamentRegistration.objects.create(
        jury=request.user,
        tournament=tournament,
        status=JuryRegistrationStatus.PENDING,
    )
    
    messages.success(request, 'Ваша заявка на участь як журі прийнята. Очікуйте схвалення адміністратора.')
    return redirect('tournament_detail', tournament_id=tournament_id)


@login_required
def tournament_dashboard(request):
    managed_team = Team.objects.filter(captain=request.user).select_related('tournament').first()
    joined_team = Team.objects.filter(memberships__user=request.user).exclude(captain=request.user).select_related('tournament').first()
    available_tournaments = Tournament.objects.all().order_by('-created_at')
    return render(request, 'tournaments/dashboard.html', {
        'managed_team': managed_team,
        'joined_team': joined_team,
        'available_tournaments': available_tournaments,
    })


@login_required
def tournament_create(request):
    if not request.user.is_admin_like and not request.user.is_superuser:
        messages.error(request, 'У вас немає прав для створення турнірів.')
        return redirect('home')

    form = TournamentForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        tournament = form.save(commit=False)
        tournament.creator = request.user
        tournament.save()
        messages.success(request, f"Турнір '{tournament.title}' створено!")
        return redirect('dashboard')

    return render(request, 'tournaments/tournament_form.html', {'form': form, 'title': 'Створення турніру'})

@login_required
def manage_access_and_jury(request):
    if request.user.role != UserRole.ADMIN:
        return redirect('dashboard')

    # Обробка дій над користувачами
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        
        if user_id and action:
            target_user = get_object_or_404(User, id=user_id)
            
            # Захист: не даємо адміну випадково змінити себе або іншого адміна/організатора через цю форму
            if target_user.role in [UserRole.ADMIN, UserRole.ORGANIZER]:
                messages.error(request, "Не можна редагувати адміністраторів через цю панель.")
            else:
                if action == 'toggle_status':
                    target_user.is_active = not target_user.is_active
                    target_user.save()
                    status_text = "активовано" if target_user.is_active else "заблоковано"
                    messages.success(request, f"Користувача {target_user.email} {status_text}.")
                
                elif action == 'make_jury':
                    target_user.role = UserRole.JURY
                    target_user.save()
                    messages.success(request, f"{target_user.email} тепер має роль Журі.")
                
                elif action == 'make_participant':
                    target_user.role = UserRole.PARTICIPANT
                    target_user.save()
                    messages.success(request, f"{target_user.email} тепер має роль Учасника.")

            return redirect('manage_access')
        
    users_to_manage = User.objects.exclude(role__in=[UserRole.ADMIN, UserRole.ORGANIZER])

    # 2. Призначення робіт
    if request.method == 'POST' and 'assign_jury' in request.POST:
        form = JuryAssignmentForm(request.POST)
        if form.is_valid():
            jury = form.cleaned_data['jury']
            submission = form.cleaned_data['submission']
            
            # Створюємо об'єкт оцінки (якщо його ще немає), щоб закріпити роботу за журі
            evaluation, created = Evaluation.objects.get_or_create(
                submission=submission,
                jury=jury
            )
            if created:
                messages.success(request, f"Роботу #{submission.id} призначено журі {jury.email}")
            else:
                messages.warning(request, "Цю роботу вже призначено цьому журі.")
            return redirect('manage_access')
    else:
        form = JuryAssignmentForm()

    context = {
        'users': users_to_manage,
        'jury_form': form,
        'assignments': Evaluation.objects.select_related('submission', 'jury').all()
    }
    return render(request, 'tournaments/manage_access.html', context)

@login_required
def tournament_edit(request, pk):
    if not request.user.is_admin_like:
        return redirect('home')

    tournament = get_object_or_404(Tournament, pk=pk)
    form = TournamentForm(request.POST or None, request.FILES or None, instance=tournament)
    file_form = TournamentFileForm()
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Параметри турніру оновлено')
        return redirect('dashboard')

    return render(request, 'tournaments/tournament_form.html', {
        'form': form,
        'file_form': file_form,
        'title': 'Редагування турніру',
        'tournament': tournament,
        'files': tournament.files.select_related('uploaded_by').all(),
    })


@login_required
def create_team(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    if request.user.role != UserRole.PARTICIPANT:
        messages.error(request, 'Тільки зареєстровані учасники можуть створювати команди.')
        return redirect('tournament_detail', tournament_id=tournament_id)

    registration_error = tournament_registration_error(tournament)
    if registration_error:
        messages.error(request, registration_error)
        return redirect('tournament_detail', tournament_id=tournament_id)

    if _get_user_tournament_team(request.user, tournament):
        messages.warning(request, 'Ви вже перебуваєте в команді на цей турнір.')
        return redirect('tournament_detail', tournament_id=tournament_id)

    if tournament.max_teams and tournament.teams.count() >= tournament.max_teams:
        messages.error(request, 'Усі місця на цей турнір уже зайняті.')
        return redirect('tournament_detail', tournament_id=tournament_id)

    if request.method == 'POST':
        team_name = (request.POST.get('team_name') or '').strip()
        if Team.objects.filter(tournament=tournament, name=team_name).exists():
            messages.error(request, f"Команда з назвою '{team_name}' вже існує в цьому турнірі. Виберіть іншу назву.")
        elif team_name:
            Team.objects.create(name=team_name, captain=request.user, tournament=tournament, captain_email=request.user.email, captain_name=request.user.full_name or request.user.nickname)
            messages.success(request, f"Команду '{team_name}' успішно створено!")
            return redirect('team_dashboard')
    return render(request, 'tournaments/create_team.html', {'tournament': tournament})


@login_required
def register_for_tournament(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    if request.user.role != UserRole.PARTICIPANT:
        messages.error(request, 'Тільки зареєстровані учасники можуть реєструвати команди.')
        return redirect('home')

    registration_error = tournament_registration_error(tournament)
    if registration_error:
        messages.error(request, registration_error)
        return redirect('tournament_detail', tournament_id=tournament_id)

    existing_team = _get_user_tournament_team(request.user, tournament)
    if existing_team:
        messages.info(request, 'Ви вже зареєстровані на цей турнір.')
        return redirect('team_dashboard')

    if tournament.max_teams and tournament.teams.count() >= tournament.max_teams:
        messages.error(request, 'Усі місця на цей турнір уже зайняті.')
        return redirect('tournament_detail', tournament_id=tournament.id)

    return redirect('create_team', tournament_id=tournament.id)


@login_required
def team_dashboard(request):
    team = Team.objects.filter(captain=request.user).select_related('tournament').first()
    if not team:
        team = Team.objects.filter(memberships__user=request.user).select_related('tournament').distinct().first()
    if not team:
        messages.info(request, 'Ви ще не перебуваєте в команді.')
        return redirect('home')

    submissions = team.submissions.select_related('round').prefetch_related('evaluation').order_by('-created_at')
    submissions = attach_submission_score_summaries(submissions)
    return render(request, 'tournaments/team_dashboard.html', {'team': team, 'submissions': submissions})


@login_required
def add_team_member(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    if request.user != team.captain:
        messages.error(request, 'Тільки капітан команди може додавати учасників.')
        return redirect('team_detail', pk=team.id)

    form = AddMemberForm(request.POST or None, team=team, user=request.user)
    if request.method == 'POST':
        if form.is_valid():
            email = form.cleaned_data['email']
            user_to_add = getattr(form, 'user_instance', None)
            TeamMember.objects.get_or_create(
                team=team,
                email=email,
                defaults={'user': user_to_add, 'full_name': getattr(user_to_add, 'full_name', '') or getattr(user_to_add, 'nickname', '') or email},
            )
            messages.success(request, f'Учасника {email} додано!')
            return redirect('team_detail', pk=team.id)
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
            return redirect('team_detail', pk=team.id)

    return render(request, 'tournaments/add_member.html', {'team': team, 'form': form})


@login_required
def team_detail(request, pk):
    team = get_object_or_404(Team.objects.select_related('captain', 'tournament'), pk=pk)
    members = TeamMember.objects.filter(team=team).order_by('full_name')
    submissions = Submission.objects.filter(team=team).select_related('round').prefetch_related('evaluation').order_by('-created_at')
    submissions = attach_submission_score_summaries(submissions)
    return render(request, 'tournaments/team_detail.html', {
        'team': team,
        'members': members,
        'submissions': submissions,
        'is_captain': team.captain == request.user,
    })


@login_required
def round_create(request, tournament_id):
    if not request.user.is_admin_like and not request.user.is_superuser:
        messages.error(request, 'У вас немає прав для створення турнірів.')
        return redirect('home')

    tournament = get_object_or_404(Tournament, id=tournament_id)
    form = RoundForm(request.POST or None, tournament=tournament)
    if request.method == 'POST' and form.is_valid():
        new_round = form.save(commit=False)
        new_round.tournament = tournament
        new_round.save()
        new_round.set_scoring_criteria(form.cleaned_data['parsed_criteria'])
        messages.success(request, f"Раунд '{new_round.title}' успішно створено!")
        return redirect('tournament_detail', tournament_id=tournament.id)
    return render(request, 'tournaments/round_form.html', {'form': form, 'tournament': tournament})


@login_required
def round_edit(request, round_id):
    if not request.user.is_admin_like and not request.user.is_superuser:
        messages.error(request, 'У вас немає прав для редагування раундів.')
        return redirect('home')

    round_obj = get_object_or_404(Round.objects.select_related('tournament'), id=round_id)
    tournament = round_obj.tournament
    form = RoundForm(request.POST or None, instance=round_obj, tournament=tournament)

    if request.method == 'POST' and form.is_valid():
        updated_round = form.save()
        messages.success(request, f"Раунд '{updated_round.title}' успішно оновлено!")
        return redirect('tournament_detail', tournament_id=tournament.id)

    return render(request, 'tournaments/round_form.html', {
        'form': form,
        'tournament': tournament,
        'round_obj': round_obj,
        'is_edit': True,
    })

@login_required
def submission_create(request, team_id):
    team = get_object_or_404(Team.objects.select_related('tournament', 'captain'), id=team_id)
    is_allowed = (
        request.user == team.captain
        or TeamMember.objects.filter(team=team, user=request.user).exists()
        or TeamMember.objects.filter(team=team, email__iexact=request.user.email).exists()
    )
    if not is_allowed:
        messages.error(request, 'Ви не маєте доступу до цієї команди.')
        return redirect('dashboard')

    form = SubmissionForm(request.POST or None, team=team)
    if request.method == 'POST' and form.is_valid():
        round_obj = form.cleaned_data['round']
        if round_obj.tournament_id != team.tournament_id:
            messages.error(request, 'Цей раунд не належить турніру вашої команди.')
            return redirect('team_detail', pk=team.id)
        if not round_obj.accepts_submissions():
            messages.error(request, 'Подання або оновлення відповіді для цього раунду вже недоступне.')
            return redirect('team_detail', pk=team.id)

        submission, created = Submission.objects.update_or_create(
            team=team,
            round=round_obj,
            defaults={
                'github_link': form.cleaned_data['github_link'],
                'video_link': form.cleaned_data['video_link'],
                'description': form.cleaned_data['description'],
            },
        )
        messages.success(request, 'Роботу успішно подано!' if created else 'Вашу попередню роботу для цього раунду було оновлено.')
        return redirect('team_detail', pk=team.id)

    return render(request, 'tournaments/submission_form.html', {'form': form, 'team': team})


@login_required
def tournament_file_upload(request, tournament_id):
    if not request.user.is_admin_like and not request.user.is_superuser:
        messages.error(request, 'У вас немає прав для завантаження файлів до турніру.')
        return redirect('home')

    tournament = get_object_or_404(Tournament, pk=tournament_id)
    if request.method != 'POST':
        return redirect('dashboard')

    form = TournamentFileForm(request.POST, request.FILES)
    if form.is_valid():
        tournament_file = form.save(commit=False)
        tournament_file.tournament = tournament
        tournament_file.uploaded_by = request.user
        tournament_file.save()
        messages.success(request, 'Файл турніру успішно завантажено.')
    else:
        for field_errors in form.errors.values():
            for error in field_errors:
                messages.error(request, error)

    return redirect('dashboard')


@login_required
def tournament_file_download(request, file_id):
    tournament_file = get_object_or_404(TournamentFile.objects.select_related('tournament'), pk=file_id)
    if not _user_can_access_tournament_files(request.user, tournament_file.tournament):
        messages.error(request, 'Файли турніру доступні лише зареєстрованим командам під час активного раунду.')
        return redirect('tournament_detail', tournament_id=tournament_file.tournament_id)
    if not tournament_file.file:
        raise Http404('Файл не знайдено.')
    return FileResponse(tournament_file.file.open('rb'), as_attachment=True, filename=tournament_file.file.name.split('/')[-1])


@login_required
def tournament_file_open(request, file_id):
    tournament_file = get_object_or_404(TournamentFile.objects.select_related('tournament'), pk=file_id)
    if not _user_can_access_tournament_files(request.user, tournament_file.tournament):
        messages.error(request, 'Файли турніру доступні лише зареєстрованим командам під час активного раунду.')
        return redirect('tournament_detail', tournament_id=tournament_file.tournament_id)
    if not tournament_file.file:
        raise Http404('Файл не знайдено.')
    return FileResponse(tournament_file.file.open('rb'), as_attachment=False, filename=tournament_file.file.name.split('/')[-1])


class TournamentFileListCreateView(APIView):
    permission_classes = [IsAuthenticatedJWT]
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsOrganizerOrAdmin()]
        return [IsAuthenticatedJWT()]

    def get(self, request, tournament_id):
        tournament = get_object_or_404(Tournament, pk=tournament_id)
        if not _user_can_access_tournament_files(request.user, tournament):
            return Response({'detail': 'Файли турніру доступні лише зареєстрованим командам під час активного раунду.'}, status=status.HTTP_403_FORBIDDEN)
        files = tournament.files.select_related('uploaded_by').all()
        return Response(TournamentFileOutSerializer(files, many=True, context={'request': request}).data)

    def post(self, request, tournament_id):
        tournament = get_object_or_404(Tournament, pk=tournament_id)
        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'detail': 'File is required'}, status=status.HTTP_400_BAD_REQUEST)

        title = (request.data.get('title') or uploaded.name).strip()
        file_type = (request.data.get('file_type') or 'general').strip()
        tournament_file = TournamentFile.objects.create(
            tournament=tournament,
            title=title,
            file_type=file_type if file_type else 'general',
            file=uploaded,
            uploaded_by=request.user,
        )
        return Response(TournamentFileOutSerializer(tournament_file, context={'request': request}).data, status=status.HTTP_201_CREATED)


@login_required
def create_staff(request):
    if request.user.role not in [UserRole.ORGANIZER, UserRole.ADMIN]:
        messages.error(request, 'Доступ заборонено.')
        return redirect('dashboard')

    if request.method == 'POST':
        email = normalize_email_value(request.POST.get('email'))
        role = (request.POST.get('role') or '').strip()
        allowed_roles = {UserRole.ADMIN, UserRole.JURY}
        if role not in allowed_roles:
            messages.error(request, 'Некоректна роль.')
            return redirect('dashboard')
        if not email:
            messages.error(request, 'Вкажіть email.')
            return redirect('dashboard')
        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'Користувач з таким email вже існує.')
            return redirect('dashboard')

        alphabet = string.ascii_letters + string.digits
        temp_password = ''.join(secrets.choice(alphabet) for _ in range(12))
        base_nickname = email.split('@')[0][:140] or 'user'
        nickname = base_nickname
        suffix = 1
        while User.objects.filter(nickname__iexact=nickname).exists():
            suffix += 1
            nickname = f'{base_nickname[:140-len(str(suffix))-1]}-{suffix}'

        new_user = User.objects.create_user(
            email=email,
            password=temp_password,
            nickname=nickname,
            role=role,
            is_verified=True,
            is_staff=(role == UserRole.ADMIN),
        )
        messages.success(request, f'Користувача {new_user.email} створено. Тимчасовий пароль: {temp_password}')

    return redirect('dashboard')


class SubmissionHistoryView(APIView):
    def get(self, request):
        stats = (
            Submission.objects.filter(user=request.user)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        
        data = {item['date'].strftime('%Y-%m-%d'): item['count'] for item in stats}
        return Response(data)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserOutSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Якщо використовується SimpleJWT з blacklist, тут можна додати логіку анулювання.
        # Для базового JWT достатньо просто повернути успішну відповідь.
        return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)




class UserMeView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def get(self, request):
        return Response(UserOutSerializer(request.user).data)

    def patch(self, request):
        allowed = {'nickname', 'full_name', 'discord_tag'}
        for field in allowed:
            if field in request.data:
                setattr(request.user, field, (request.data.get(field) or '').strip())
        request.user.save(update_fields=[field for field in allowed if field in request.data])
        return Response(UserOutSerializer(request.user).data)

class UserProfileImageUploadView(APIView):
    permission_classes = [IsAuthenticatedJWT]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'detail': 'File is required'}, status=status.HTTP_400_BAD_REQUEST)
        content = process_square_image(file)
        request.user.profile_image.save(content.name, content, save=True)
        return Response(UserOutSerializer(request.user).data)


class MyTeamInfoView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def get(self, request):
        teams = (
            Team.objects.filter(captain=request.user)
            | Team.objects.filter(memberships__user=request.user)
        )
        teams = teams.distinct().select_related('tournament').annotate(members_count=Count('memberships')).prefetch_related('memberships').order_by('name')
        return Response(TeamOutSerializer(teams, many=True).data)


class MyEvaluationsView(APIView):
    permission_classes = [IsJury]

    def get(self, request):
        evaluations = (
            Evaluation.objects.filter(jury=request.user)
            .select_related('submission__team', 'submission__round', 'submission__round__tournament')
            .prefetch_related('criteria_scores__criterion')
            .order_by('submission__round__title', 'submission__team__name', '-created_at')
        )
        return Response(EvaluationOutSerializer(evaluations, many=True).data)


class EvaluationDetailUpdateView(APIView):
    permission_classes = [IsJury]

    def get_object(self, request, evaluation_id):
        return get_object_or_404(
            Evaluation.objects
            .filter(jury=request.user)
            .select_related('submission__team', 'submission__round', 'submission__round__tournament')
            .prefetch_related('criteria_scores__criterion'),
            pk=evaluation_id,
        )

    def get(self, request, evaluation_id):
        evaluation = self.get_object(request, evaluation_id)
        evaluation.ensure_score_entries()
        return Response(EvaluationOutSerializer(evaluation).data)

    def patch(self, request, evaluation_id):
        evaluation = self.get_object(request, evaluation_id)
        criteria_scores = evaluation.ensure_score_entries()
        scores_by_criterion = {item.criterion_id: item for item in criteria_scores}

        for item in request.data.get('criteria_scores', []):
            try:
                criterion_id = int(item.get('criterion_id'))
            except (TypeError, ValueError):
                return Response({'detail': 'Invalid criterion'}, status=status.HTTP_400_BAD_REQUEST)
            if criterion_id not in scores_by_criterion:
                return Response({'detail': 'Invalid criterion'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                score_value = float(item.get('score') or 0)
            except (TypeError, ValueError):
                return Response({'detail': 'Invalid score'}, status=status.HTTP_400_BAD_REQUEST)
            criterion_score = scores_by_criterion[criterion_id]
            if score_value < 0 or score_value > criterion_score.criterion.max_score:
                return Response({'detail': 'Score is outside criterion range'}, status=status.HTTP_400_BAD_REQUEST)

            criterion_score.score = score_value
            criterion_score.save(update_fields=['score'])

        if 'comment' in request.data:
            evaluation.comment = request.data.get('comment') or ''
            evaluation.save(update_fields=['comment'])

        evaluation = Evaluation.objects.select_related(
            'submission__team',
            'submission__round',
            'submission__round__tournament',
        ).prefetch_related('criteria_scores__criterion').get(pk=evaluation.pk)
        return Response(EvaluationOutSerializer(evaluation).data)


class TeamDetailAPIView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def get(self, request, team_id):
        team = get_object_or_404(
            Team.objects.select_related('captain', 'tournament')
            .annotate(members_count=Count('memberships'))
            .prefetch_related('memberships'),
            pk=team_id,
        )
        team_payload = TeamOutSerializer(team).data
        team_payload['tournament'] = {
            'id': team.tournament_id,
            'title': team.tournament.title,
            'status': team.tournament.status,
        }
        team_payload['is_captain'] = team.captain_id == request.user.id
        team_payload['status'] = 'completed' if team.tournament.end_time <= timezone.now() else 'in-progress'

        rounds = Round.objects.filter(tournament=team.tournament).order_by('start_time', 'id')
        active_round = rounds.filter(start_time__lte=timezone.now(), end_time__gte=timezone.now()).first()
        team_payload['current_round_id'] = active_round.id if active_round else (rounds.first().id if rounds.exists() else None)
        team_payload['rounds'] = RoundCreateSerializer(rounds, many=True).data

        submissions = Submission.objects.filter(team=team).select_related('round').prefetch_related('evaluation').order_by('-created_at')
        team_payload['submissions'] = [
            {
                'id': submission.id,
                'round': submission.round_id,
                'roundTitle': submission.round.title,
                'createdAt': submission.created_at,
                'githubLink': submission.github_link,
                'videoLink': submission.video_link,
                'description': submission.description,
                'totalAvg': submission.total_avg,
                'rawTotal': submission.raw_total,
                'maxTotal': submission.max_total,
                'criteriaPreview': submission.criteria_preview,
            }
            for submission in attach_submission_score_summaries(submissions)
        ]
        return Response(team_payload)


class TeamMemberListCreateView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def post(self, request, team_id):
        team = get_object_or_404(Team.objects.select_related('captain', 'tournament'), pk=team_id)
        if team.captain_id != request.user.id:
            return Response({'detail': 'Only the team captain can add members'}, status=status.HTTP_403_FORBIDDEN)

        registration_error = tournament_registration_error(team.tournament, now=timezone.now())
        if registration_error:
            return Response({'detail': registration_error}, status=status.HTTP_400_BAD_REQUEST)

        if team.memberships.count() + 1 >= team.tournament.max_team_members:
            return Response({'detail': 'Team member limit reached'}, status=status.HTTP_400_BAD_REQUEST)

        email = normalize_email_value(request.data.get('email') or '')
        if not email:
            return Response({'email': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)

        if Team.objects.filter(tournament=team.tournament, captain_email=email).exists() or TeamMember.objects.filter(team__tournament=team.tournament, email=email).exists():
            return Response({'detail': 'User is already registered in this tournament'}, status=status.HTTP_400_BAD_REQUEST)

        linked_user = User.objects.filter(email__iexact=email).first()
        member = TeamMember.objects.create(
            team=team,
            email=email,
            full_name=request.data.get('full_name') or email,
            user=linked_user,
        )
        return Response({'id': member.id, 'full_name': member.full_name, 'email': member.email, 'user_id': member.user_id}, status=status.HTTP_201_CREATED)


class TeamMemberDetailView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def delete(self, request, team_id, member_id):
        team = get_object_or_404(Team.objects.select_related('captain', 'tournament'), pk=team_id)
        if team.captain_id != request.user.id:
            return Response({'detail': 'Only the team captain can remove members'}, status=status.HTTP_403_FORBIDDEN)

        registration_error = tournament_registration_error(team.tournament, now=timezone.now())
        if registration_error:
            return Response({'detail': registration_error}, status=status.HTTP_400_BAD_REQUEST)

        member = get_object_or_404(TeamMember, pk=member_id, team=team)
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminTeamDetailView(APIView):
    permission_classes = [IsAdmin]

    # Видалити команду повністю
    def delete(self, request, team_id):
        team = get_object_or_404(Team, pk=team_id)
        team.delete()
        return Response({"detail": "Команду видалено з турніру"}, status=status.HTTP_204_NO_CONTENT)


class AdminMemberDeleteView(APIView):
    permission_classes = [IsAdmin]

    # Видалити конкретного учасника з команди
    def delete(self, request, member_id):
        member = get_object_or_404(TeamMember, pk=member_id)
        # Перевірка: якщо це був останній учасник, можна або видалити команду, 
        # або просто дозволити видалення.
        member.delete()
        return Response({"detail": "Учасника видалено"}, status=status.HTTP_204_NO_CONTENT)
    

class TournamentListCreateView(APIView):
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsOrganizerOrAdmin()]
        return [AllowAny()]

    def get(self, request):
        tournaments = Tournament.objects.annotate(teams_count=Count('teams')).order_by('-created_at', '-id')
        return Response(TournamentOutSerializer(tournaments, many=True).data)

    def post(self, request):
        serializer = TournamentCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        tournament = serializer.save()
        tournament.teams_count = tournament.teams.count()
        return Response(TournamentOutSerializer(tournament).data, status=status.HTTP_201_CREATED)


class TournamentDetailUpdateView(APIView):
    def get_permissions(self):
        if self.request.method in {'PATCH', 'PUT'}:
            return [IsOrganizerOrAdmin()]
        return [AllowAny()]

    def get(self, request, tournament_id):
        tournament = get_object_or_404(Tournament.objects.annotate(teams_count=Count('teams')), pk=tournament_id)
        return Response(TournamentOutSerializer(tournament).data)

    def patch(self, request, tournament_id):
        tournament = get_object_or_404(Tournament.objects.annotate(teams_count=Count('teams')), pk=tournament_id)
        serializer = TournamentCreateSerializer(tournament, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        tournament = serializer.save()
        tournament.teams_count = tournament.teams.count()
        return Response(TournamentOutSerializer(tournament).data)

    def put(self, request, tournament_id):
        tournament = get_object_or_404(Tournament.objects.annotate(teams_count=Count('teams')), pk=tournament_id)
        serializer = TournamentCreateSerializer(tournament, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        tournament = serializer.save()
        tournament.teams_count = tournament.teams.count()
        return Response(TournamentOutSerializer(tournament).data)


class TournamentStatusUpdateView(APIView):
    permission_classes = [IsOrganizerOrAdmin]

    def patch(self, request, tournament_id):
        tournament = Tournament.objects.filter(pk=tournament_id).first()
        if not tournament:
            return Response({'detail': 'Tournament not found'}, status=status.HTTP_404_NOT_FOUND)
        new_status = request.data.get('status') or request.query_params.get('status')
        if new_status not in TournamentStatus.values:
            return Response({'detail': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        tournament.status = new_status
        tournament.save(update_fields=['status'])
        tournament.teams_count = tournament.teams.count()
        return Response(TournamentOutSerializer(tournament).data)


class TournamentImageUploadView(APIView):
    permission_classes = [IsOrganizerOrAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, tournament_id):
        tournament = Tournament.objects.filter(pk=tournament_id).first()
        if not tournament:
            return Response({'detail': 'Tournament not found'}, status=status.HTTP_404_NOT_FOUND)
        file = request.FILES.get('file')
        if not file:
            return Response({'detail': 'File is required'}, status=status.HTTP_400_BAD_REQUEST)
        content = validate_raw_image(file)
        tournament.cover_image.save(content.name, content, save=True)
        tournament.teams_count = tournament.teams.count()
        return Response(TournamentOutSerializer(tournament).data)


def tournament_leaderboard(request, tournament_id):
    """Web view for tournament leaderboard."""
    tournament = get_object_or_404(Tournament, id=tournament_id)
    teams = Team.objects.filter(tournament=tournament).prefetch_related('submissions__evaluation')
    payload = []

    for team in teams:
        submissions = list(team.submissions.all())
        all_evaluations = [submission.evaluation for submission in submissions if hasattr(submission, 'evaluation')]

        round_scores = []  # List of scores per round
        all_criteria = {}  # {criterion_name: list of scores across rounds}
        criteria_order = []
        
        for submission in submissions:
            score_data = submission.calculate_final_score()
            if score_data['total'] is not None:
                round_scores.append(score_data['total'])
            
            # Track criteria across all rounds
            for criterion in score_data['criteria']:
                if criterion['name'] not in all_criteria:
                    criteria_order.append(criterion['name'])
                    all_criteria[criterion['name']] = []
                all_criteria[criterion['name']].append(criterion['average'])

        # Calculate averages and totals
        average_score = (sum(round_scores) / len(round_scores)) if round_scores else 0.0
        total_raw_score = sum(round_scores)
        
        # Build criteria summary with per-round details
        criteria_summary = []
        for name in criteria_order:
            scores = all_criteria[name]
            criteria_summary.append({
                'name': name,
                'average': round(sum(scores) / len(scores), 2),
                'round_scores': scores,
                'rounds_participated': len(scores),
            })
        
        primary_criterion_avg = criteria_summary[0]['average'] if criteria_summary else 0.0
        payload.append({
            'team': team,
            'team_name': team.name,
            'average_score': round(average_score, 2),
            'total_raw_score': round(total_raw_score, 2),
            'round_scores': round_scores,
            'criteria_summary': criteria_summary,
            'primary_criterion_avg': round(primary_criterion_avg, 2),
            'submissions_count': len(submissions),
            'evaluations_count': len(all_evaluations),
            'rounds_scored': len(round_scores),
        })

    payload.sort(
        key=lambda x: (
            -x['average_score'],
            -x['primary_criterion_avg'],
            -x['rounds_scored'],
            -x['submissions_count'],
            x['team_name'].lower(),
        )
    )
    for index, row in enumerate(payload, start=1):
        row['rank'] = index
    
    tournament_finished = tournament.end_time <= timezone.now() or tournament.status in {
        TournamentStatus.CLOSED,
        TournamentStatus.ARCHIVED,
    }
    
    return render(request, 'tournaments/leaderboard.html', {
        'tournament': tournament,
        'leaderboard': payload,
        'is_final': tournament_finished,
    })


class TournamentLeaderboardView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, tournament_id):
        tournament = get_object_or_404(Tournament, pk=tournament_id)
        teams = Team.objects.filter(tournament=tournament).prefetch_related('submissions__evaluation')
        payload = []

        for team in teams:
            submissions = list(team.submissions.all())
            all_evaluations = [submission.evaluation for submission in submissions if hasattr(submission, 'evaluation')]

            round_scores = []  # List of scores per round
            all_criteria = {}  # {criterion_name: list of scores across rounds}
            criteria_order = []
            
            for submission in submissions:
                score_data = submission.calculate_final_score()
                if score_data['total'] is not None:
                    round_scores.append(score_data['total'])
                
                # Track criteria across all rounds
                for criterion in score_data['criteria']:
                    if criterion['name'] not in all_criteria:
                        criteria_order.append(criterion['name'])
                        all_criteria[criterion['name']] = []
                    all_criteria[criterion['name']].append(criterion['average'])

            # Calculate averages and totals
            average_score = (sum(round_scores) / len(round_scores)) if round_scores else 0.0
            total_raw_score = sum(round_scores)
            
            # Build criteria summary with per-round details
            criteria_summary = []
            for name in criteria_order:
                scores = all_criteria[name]
                criteria_summary.append({
                    'name': name,
                    'average': round(sum(scores) / len(scores), 2),
                    'round_scores': scores,
                    'rounds_participated': len(scores),
                })
            
            primary_criterion_avg = criteria_summary[0]['average'] if criteria_summary else 0.0
            payload.append({
                'team_name': team.name,
                'average_score': round(average_score, 2),
                'total_raw_score': round(total_raw_score, 2),
                'round_scores': round_scores,
                'criteria_summary': criteria_summary,
                'primary_criterion_avg': round(primary_criterion_avg, 2),
                'submissions_count': len(submissions),
                'evaluations_count': len(all_evaluations),
                'rounds_scored': len(round_scores),
            })

        payload.sort(
            key=lambda x: (
                -x['average_score'],
                -x['primary_criterion_avg'],
                -x['rounds_scored'],
                -x['submissions_count'],
                x['team_name'].lower(),
            )
        )
        for index, row in enumerate(payload, start=1):
            row['rank'] = index
        tournament_finished = tournament.end_time <= timezone.now() or tournament.status in {
            TournamentStatus.CLOSED,
            TournamentStatus.ARCHIVED,
        }
        return Response({
            'tournament_id': tournament.id,
            'tournament_title': tournament.title,
            'is_final': tournament_finished,
            'leaderboard': payload,
        })


class TournamentTeamsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, tournament_id):
        tournament = get_object_or_404(Tournament, pk=tournament_id)
        user = request.user
        can_manage = bool(getattr(user, 'is_authenticated', False) and (user.is_superuser or getattr(user, 'is_admin_like', False)))

        if tournament.hide_teams_until_registration_end and timezone.now() < tournament.reg_end and not can_manage:
            return Response([])

        teams = (
            Team.objects.filter(tournament=tournament)
            .select_related('captain')
            .annotate(members_count=Count('memberships'))
            .prefetch_related('memberships')
            .order_by('name', 'id')
        )
        return Response(TeamOutSerializer(teams, many=True).data)


class TeamCreateView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def post(self, request):
        serializer = TeamCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        team = serializer.save()
        team = Team.objects.annotate(members_count=Count('memberships')).prefetch_related('memberships').get(pk=team.pk)
        return Response(TeamOutSerializer(team).data, status=status.HTTP_201_CREATED)


class TeamImageUploadView(APIView):
    permission_classes = [IsAuthenticatedJWT]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, team_id):
        team = Team.objects.filter(pk=team_id).first()
        if not team:
            return Response({'detail': 'Team not found'}, status=status.HTTP_404_NOT_FOUND)
        file = request.FILES.get('file')
        if not file:
            return Response({'detail': 'File is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not hasattr(team, 'image'):
            return Response({'detail': 'Team image field is not configured'}, status=status.HTTP_400_BAD_REQUEST)
        content = process_square_image(file)
        team.image.save(content.name, content, save=True)
        return Response(TeamOutSerializer(team).data)


class MemberTournamentsView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def get(self, request, email):
        members = TeamMember.objects.filter(email=email).select_related('team__tournament')
        result = []
        for member in members:
            team = member.team
            tournament = team.tournament
            result.append({
                'team_id': team.id,
                'team_name': team.name,
                'tournament_id': tournament.id,
                'tournament_title': tournament.title,
                'tournament_status': tournament.status,
            })
        return Response(result)


class RoundCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsOrganizerOrAdmin()]
        return [AllowAny()]

    def get(self, request):
        tournament_id = request.query_params.get('tournament_id')
        rounds = Round.objects.select_related('tournament').order_by('start_time', 'id')
        if tournament_id:
            rounds = rounds.filter(tournament_id=tournament_id)

        user = request.user
        can_manage = bool(getattr(user, 'is_authenticated', False) and (user.is_superuser or getattr(user, 'is_admin_like', False)))
        if not can_manage:
            rounds = rounds.filter(end_time__lte=timezone.now())

        return Response(RoundCreateSerializer(rounds, many=True).data)

    def post(self, request):
        serializer = RoundCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        round_obj = serializer.save()
        return Response(serializer.to_representation(round_obj), status=status.HTTP_201_CREATED)


class RoundDetailView(APIView):
    permission_classes = [IsOrganizerOrAdmin]

    def get(self, request, round_id):
        round_obj = get_object_or_404(Round.objects.select_related('tournament'), pk=round_id)
        return Response(RoundCreateSerializer(round_obj).data)

    def patch(self, request, round_id):
        round_obj = get_object_or_404(Round, pk=round_id)
        serializer = RoundCreateSerializer(round_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        round_obj = serializer.save()
        return Response(serializer.to_representation(round_obj))

    def put(self, request, round_id):
        round_obj = get_object_or_404(Round, pk=round_id)
        serializer = RoundCreateSerializer(round_obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        round_obj = serializer.save()
        return Response(serializer.to_representation(round_obj))


class DistributeWorksView(APIView):
    permission_classes = [IsOrganizerOrAdmin]

    def post(self, request, round_id):
        round_obj = Round.objects.filter(pk=round_id).first()
        if not round_obj:
            return Response({'detail': 'Round not found'}, status=status.HTTP_404_NOT_FOUND)

        if round_obj.end_time > timezone.now() and round_obj.status != RoundStatus.CLOSED:
            return Response(
                {'detail': 'Розподіл робіт доступний лише після завершення раунду.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        evaluations_per_submission = int(request.data.get('evaluations_per_submission', 3))
        try:
            result = _distribute_round_assignments(round_obj, evaluations_per_submission=evaluations_per_submission)
        except ValueError:
            return Response({'detail': 'Немає зареєстрованих членів журі'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'Роботи розподілено між журі',
            'evaluations_per_submission': result['evaluations_per_submission'],
            'evaluations_created_count': result['evaluations_created_count'],
            'submissions_count': result['submissions_count'],
            'juries_assigned': result['juries_assigned'],
        })


class ActiveTaskView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def get(self, request):
        # 1. Знаходимо команду користувача
        member = TeamMember.objects.filter(email=request.user.email).first()
        if not member or not member.team:
            return Response({'detail': 'Ви не є членом жодної команди'}, status=404)
        
        # 2. Знаходимо активний раунд турніру цієї команди
        tournament = member.team.tournament
        active_round = Round.objects.filter(
            tournament=tournament,
            status=RoundStatus.ACTIVE,
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        ).first()

        if not active_round:
            return Response({'detail': 'На даний момент немає активних завдань'}, status=404)

        serializer = RoundCreateSerializer(active_round)
        return Response(serializer.data)

# ===================SUBMISSION / JURY====================

def _distribute_round_assignments(round_obj, evaluations_per_submission=3):
    """
    Distribute submissions to jury members for evaluation.
    
    Args:
        round_obj: The Round to distribute submissions for
        evaluations_per_submission: Number of jury members per submission (default 3)
    
    Returns:
        dict with distribution statistics
    """
    submissions = list(Submission.objects.filter(round=round_obj))
    jury_members = list(User.objects.filter(role=UserRole.JURY, jury_tournaments=round_obj.tournament))
    if not jury_members:
        raise ValueError('Немає зареєстрованих членів журі')

    evaluations_created_count = 0
    for submission in submissions:
        criteria = submission.round.get_or_create_scoring_criteria()
        chosen_jury = random.choice(jury_members)
        evaluation, was_created = Evaluation.objects.get_or_create(
            submission=submission,
            defaults={'jury': chosen_jury},
        )
        evaluation.ensure_score_entries(criteria)
        evaluations_created_count += int(was_created)

    return {
        'evaluations_per_submission': evaluations_per_submission,
        'evaluations_created_count': evaluations_created_count,
        'submissions_count': len(submissions),
        'juries_assigned': len([s for s in submissions if hasattr(s, 'evaluation')]),
    }


def _auto_distribute_if_round_started(round_obj, evaluations_per_submission=3):
    """Automatically distribute round assignments if round has finished."""
    if round_obj.end_time > timezone.now() and round_obj.status != RoundStatus.CLOSED:
        return None

    return _distribute_round_assignments(round_obj, evaluations_per_submission=evaluations_per_submission)

class SubmissionCreateView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def post(self, request):
        serializer = SubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()
        return Response(serializer.to_representation(submission), status=status.HTTP_201_CREATED)


class JuryTournamentRegistrationView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def get(self, request):
        if request.user.role != UserRole.JURY:
            return Response({'detail': 'Тільки член журі може переглядати свої заявки.'}, status=status.HTTP_403_FORBIDDEN)
        registrations = JuryTournamentRegistration.objects.filter(jury=request.user).select_related('tournament', 'reviewed_by')
        return Response(JuryTournamentRegistrationOutSerializer(registrations, many=True).data)

    def post(self, request):
        if request.user.role != UserRole.JURY:
            return Response({'detail': 'Тільки член журі може подати заявку.'}, status=status.HTTP_403_FORBIDDEN)

        tournament_id = request.data.get('tournament_id')
        tournament = Tournament.objects.filter(pk=tournament_id).first()
        if not tournament:
            return Response({'detail': 'Tournament not found'}, status=status.HTTP_404_NOT_FOUND)

        registration, created = JuryTournamentRegistration.objects.get_or_create(
            jury=request.user,
            tournament=tournament,
            defaults={'status': JuryRegistrationStatus.PENDING},
        )
        if not created and registration.status == JuryRegistrationStatus.REJECTED:
            registration.status = JuryRegistrationStatus.PENDING
            registration.reviewed_by = None
            registration.reviewed_at = None
            registration.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])

        if registration.status == JuryRegistrationStatus.APPROVED:
            request.user.jury_tournaments.add(tournament)

        code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(JuryTournamentRegistrationOutSerializer(registration).data, status=code)


class JuryTournamentRegistrationReviewView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def patch(self, request, registration_id):
        if not (request.user.is_superuser or request.user.role == UserRole.ADMIN):
            return Response({'detail': 'Тільки адміністратор може підтверджувати заявки.'}, status=status.HTTP_403_FORBIDDEN)

        registration = JuryTournamentRegistration.objects.filter(pk=registration_id).select_related('jury', 'tournament').first()
        if not registration:
            return Response({'detail': 'Registration not found'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        if new_status not in {JuryRegistrationStatus.APPROVED, JuryRegistrationStatus.REJECTED}:
            return Response({'detail': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

        registration.status = new_status
        registration.reviewed_by = request.user
        registration.reviewed_at = timezone.now()
        registration.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])

        if new_status == JuryRegistrationStatus.APPROVED:
            registration.jury.jury_tournaments.add(registration.tournament)
        else:
            registration.jury.jury_tournaments.remove(registration.tournament)

        return Response(JuryTournamentRegistrationOutSerializer(registration).data)


class JuryPendingRegistrationsView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def get(self, request):
        if not (request.user.is_superuser or request.user.role == UserRole.ADMIN):
            return Response({'detail': 'Тільки адміністратор може переглядати заявки.'}, status=status.HTTP_403_FORBIDDEN)
        registrations = (
            JuryTournamentRegistration.objects
            .filter(status=JuryRegistrationStatus.PENDING)
            .select_related('jury', 'tournament')
        )
        return Response(JuryTournamentRegistrationOutSerializer(registrations, many=True).data)


class MyAssignedJuryTournamentsView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def get(self, request):
        if request.user.role != UserRole.JURY:
            return Response({'detail': 'Тільки для членів журі.'}, status=status.HTTP_403_FORBIDDEN)
        tournaments = request.user.jury_tournaments.annotate(teams_count=Count('teams')).order_by('-created_at', '-id')
        return Response(TournamentOutSerializer(tournaments, many=True).data)

@login_required
def evaluation_detail(request, eval_id):
    if request.user.role != UserRole.JURY:
        return redirect('dashboard')

    evaluation = get_object_or_404(
        Evaluation.objects.select_related('submission__team', 'submission__round'),
        pk=eval_id,
        jury=request.user,
    )
    criteria_scores = evaluation.ensure_score_entries()

    if request.method == 'POST':
        comment = request.POST.get('comment', '').strip()

        errors = []
        parsed_scores = []
        for criterion_score in criteria_scores:
            raw_value = request.POST.get(f'criterion_{criterion_score.criterion_id}', '').strip()
            try:
                value = float(raw_value)
            except ValueError:
                errors.append(f'Введіть числове значення для "{criterion_score.criterion.name}".')
                continue
            if not (0 <= value <= criterion_score.criterion.max_score):
                errors.append(
                    f'Оцінка для "{criterion_score.criterion.name}" має бути від 0 до {criterion_score.criterion.max_score}.'
                )
            parsed_scores.append((criterion_score, value))

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            for criterion_score, value in parsed_scores:
                criterion_score.score = value
                criterion_score.save(update_fields=['score'])
            evaluation.comment = comment
            evaluation.save()
            messages.success(request, 'Оцінку збережено!')
            return redirect('dashboard')

    return render(request, 'tournaments/evaluation_detail.html', {
        'evaluation': evaluation,
        'criteria_scores': criteria_scores,
        'criteria_total': sum(item.score for item in criteria_scores),
        'criteria_max_total': sum(item.criterion.max_score for item in criteria_scores),
        'criteria_definition': _criteria_definition_from_round(evaluation.submission.round),
    })

