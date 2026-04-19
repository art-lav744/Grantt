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
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import AddMemberForm, ProfileEditForm, RegisterForm, RoundForm, SubmissionForm, TournamentForm
from .models import Evaluation, Round, RoundStatus, Submission, Team, TeamMember, Tournament, TournamentStatus, User, UserRole
from .permissions import IsAdmin, IsAuthenticatedJWT, IsJury, IsOrganizerOrAdmin
from .serializers import (
    EvaluationOutSerializer,
    LoginSerializer,
    RegisterSerializer,
    RoundCreateSerializer,
    SubmissionCreateSerializer,
    TeamCreateSerializer,
    TeamOutSerializer,
    TournamentCreateSerializer,
    TournamentOutSerializer,
    UserOutSerializer,
)
from .utils import (
    attach_submission_score_summaries,
    normalize_email_value,
    process_square_image,
    tournament_registration_error,
    validate_raw_image,
)


def home(request):
    now = timezone.now()
    context = {
        'reg_open': Tournament.objects.filter(reg_start__lte=now, reg_end__gte=now),
        'running': Tournament.objects.filter(start_time__lte=now, end_time__gte=now),
        'finished': Tournament.objects.filter(end_time__lt=now),
        'upcoming': Tournament.objects.filter(reg_start__gt=now),
    }
    return render(request, 'home.html', context)



def index(request):
    now = timezone.now()
    context = {
        'reg_open': Tournament.objects.filter(reg_start__lte=now, reg_end__gte=now),
        'running': Tournament.objects.filter(start_time__lte=now, end_time__gte=now),
        'finished': Tournament.objects.filter(end_time__lt=now),
        'now': now,
    }
    return render(request, 'index.html', context)



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
        .select_related('team', 'round', 'team__tournament')
        .prefetch_related('evaluations')
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
        context['tournaments'] = Tournament.objects.all().annotate(teams_count=Count('teams'))
        return render(request, 'dashboards/admin_dashboard.html', context)

    if user.role == UserRole.ORGANIZER:
        context['my_tournaments'] = Tournament.objects.filter(creator=user).annotate(teams_count=Count('teams'))
        context['total_users'] = User.objects.count()
        context['tournaments'] = Tournament.objects.all().annotate(teams_count=Count('teams'))
        context['my_evaluations'] = Evaluation.objects.filter(jury=user).select_related('submission__team', 'submission__round')
        return render(request, 'dashboards/organizer_dashboard.html', context)

    if user.role == UserRole.JURY:
        evals = Evaluation.objects.filter(jury=user).select_related('submission__team', 'submission__round').order_by('submission__round__title', 'submission__team__name')
        total_count = evals.count()
        done_count = sum(1 for e in evals if e.tech_score > 0 or e.func_score > 0)
        context.update({'my_evaluations': evals, 'total_count': total_count, 'done_count': done_count, 'pending_count': total_count - done_count})
        return render(request, 'dashboards/jury_dashboard.html', context)

    captain_teams, member_teams = _get_user_all_teams(user)
    all_my_teams = (captain_teams | member_teams).distinct()
    context['my_teams'] = all_my_teams
    selected_team_id = request.GET.get('team_id')
    if selected_team_id:
        selected_team = all_my_teams.filter(id=selected_team_id).first()
        if selected_team:
            context.update({
                'selected_team': selected_team,
                'members': selected_team.memberships.all(),
                'submissions': Submission.objects.filter(team=selected_team).select_related('round').order_by('-created_at'),
                'form': SubmissionForm(team=selected_team),
            })
    return render(request, 'dashboards/team_dashboard.html', context)



def tournament_list(request):
    tournaments = Tournament.objects.all().order_by('-created_at', '-id')
    return render(request, 'tournaments/tournament_list.html', {'tournaments': tournaments})



def tournament_detail(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    teams = tournament.teams.select_related('captain').all()
    rounds = tournament.rounds.order_by('start_time')
    user_team = _get_user_tournament_team(request.user, tournament)
    return render(request, 'tournaments/tournament_detail.html', {
        'tournament': tournament,
        'teams': teams,
        'rounds': rounds,
        'user_team': user_team,
    })


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
def tournament_edit(request, pk):
    if not request.user.is_admin_like:
        return redirect('home')

    tournament = get_object_or_404(Tournament, pk=pk)
    form = TournamentForm(request.POST or None, request.FILES or None, instance=tournament)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Параметри турніру оновлено')
        return redirect('dashboard')

    return render(request, 'tournaments/tournament_form.html', {'form': form, 'title': 'Редагування турніру', 'tournament': tournament})


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

    submissions = team.submissions.select_related('round').prefetch_related('evaluations').order_by('-created_at')
    submissions = attach_submission_score_summaries(submissions)
    return render(request, 'tournaments/team_dashboard.html', {'team': team, 'submissions': submissions})


@login_required
def add_team_member(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    if request.user != team.captain:
        messages.error(request, 'Тільки капітан команди може додавати учасників.')
        return redirect('team_detail', pk=team.id)

    if not ensure_registration_open(team.tournament, raise_exception=False):
        messages.error(request, 'Реєстрація на турнір вже закінчилася. Ви не можете додавати нових учасників.')
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
    submissions = Submission.objects.filter(team=team).select_related('round').prefetch_related('evaluations').order_by('-created_at')
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
        messages.success(request, f"Раунд '{new_round.title}' успішно створено!")
        return redirect('tournament_detail', tournament_id=tournament.id)
    return render(request, 'tournaments/round_form.html', {'form': form, 'tournament': tournament})


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
        if round_obj.end_time < timezone.now() or timezone.now() < round_obj.start_time:
            messages.error(request, 'Сабміт для цього раунду вже закритий!')
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
        teams = Team.objects.filter(captain=request.user).order_by('name')
        return Response(TeamOutSerializer(teams, many=True).data)


class MyEvaluationsView(APIView):
    permission_classes = [IsJury]

    def get(self, request):
        evaluations = Evaluation.objects.filter(jury=request.user).order_by('-created_at')
        return Response(EvaluationOutSerializer(evaluations, many=True).data)


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


class TournamentLeaderboardView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, tournament_id):
        results = Team.objects.filter(tournament_id=tournament_id).annotate(
            tech_avg=Avg('submissions__evaluations__tech_score'),
            func_avg=Avg('submissions__evaluations__func_score'),
            submissions_count=Count('submissions', distinct=True),
        )
        payload = []
        for team in results:
            tech_avg = round(float(team.tech_avg or 0), 2)
            func_avg = round(float(team.func_avg or 0), 2)
            total_score = round((tech_avg + func_avg) / 2, 2)
            payload.append({
                'team_name': team.name,
                'tech_avg': tech_avg,
                'func_avg': func_avg,
                'total_score': total_score,
                'submissions_count': team.submissions_count,
            })
        payload.sort(key=lambda x: x['total_score'], reverse=True)
        return Response(payload)


class TeamCreateView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def post(self, request):
        serializer = TeamCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        team = serializer.save()
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
    permission_classes = [IsOrganizerOrAdmin]

    def post(self, request):
        serializer = RoundCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        round_obj = serializer.save()
        return Response(serializer.to_representation(round_obj), status=status.HTTP_201_CREATED)


class DistributeWorksView(APIView):
    permission_classes = [IsOrganizerOrAdmin]

    def post(self, request, round_id):
        round_obj = Round.objects.filter(pk=round_id).first()
        if not round_obj:
            return Response({'detail': 'Round not found'}, status=status.HTTP_404_NOT_FOUND)

        K = int(request.data.get('k', 3))
        try:
            result = _distribute_round_assignments(round_obj, k=K)
        except ValueError:
            return Response({'detail': 'Немає зареєстрованих членів журі'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'Роботи розподілено між журі',
            'k_per_submission': result['k_per_submission'],
            'created_assignments': result['created_assignments'],
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

def _distribute_round_assignments(round_obj, k=3):
    submissions = list(Submission.objects.filter(round=round_obj))
    jury_members = list(User.objects.filter(role=UserRole.JURY, jury_tournaments=round_obj.tournament))
    if not jury_members:
        raise ValueError('Немає зареєстрованих членів журі')

    k_actual = min(k, len(jury_members))
    created = 0
    for submission in submissions:
        chosen = random.sample(jury_members, k=k_actual)
        for jury in chosen:
            _, was_created = Evaluation.objects.get_or_create(
                submission=submission,
                jury=jury,
                defaults={'tech_score': 0, 'func_score': 0},
            )
            created += int(was_created)

    return {
        'k_per_submission': k_actual,
        'created_assignments': created,
        'submissions_count': len(submissions),
    }


def _auto_distribute_if_round_started(round_obj, k=3):
    if round_obj.start_time > timezone.now():
        return None

    return _distribute_round_assignments(round_obj, k=k)

class SubmissionCreateView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def post(self, request):
        serializer = SubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()

        # Якщо раунд уже стартував, одразу запускаємо той самий алгоритм,
        # що і в POST /api/rounds/<id>/distribute.
        try:
            _auto_distribute_if_round_started(submission.round, k=3)
        except ValueError:
            # Якщо журі ще не призначене - ігноруєм
            pass

        return Response(serializer.to_representation(submission), status=status.HTTP_201_CREATED)

@login_required
def evaluation_detail(request, eval_id):
    if request.user.role != UserRole.JURY:
        return redirect('dashboard')

    evaluation = get_object_or_404(
        Evaluation.objects.select_related('submission__team', 'submission__round'),
        pk=eval_id,
        jury=request.user,
    )

    if request.method == 'POST':
        tech  = request.POST.get('tech_score', '').strip()
        func  = request.POST.get('func_score', '').strip()
        comment = request.POST.get('comment', '').strip()

        errors = []
        try:
            tech_val = float(tech)
            func_val = float(func)
        except ValueError:
            errors.append('Введіть числові значення оцінок.')

        if not errors:
            if not (0 <= tech_val <= 100) or not (0 <= func_val <= 100):
                errors.append('Оцінки мають бути від 0 до 100.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            evaluation.tech_score = tech_val
            evaluation.func_score = func_val
            evaluation.comment    = comment
            evaluation.save()
            messages.success(request, 'Оцінку збережено!')
            return redirect('dashboard')

    return render(request, 'tournaments/evaluation_detail.html', {'evaluation': evaluation})


