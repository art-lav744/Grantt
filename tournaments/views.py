import random
import string
import secrets
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.utils import timezone

from .forms import RegisterForm, SubmissionForm, TeamMemberForm, TournamentForm
from .models import Evaluation, Round, Submission, Team, TeamMember, Tournament, TournamentStatus, User, UserRole
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
from .utils import process_square_image, validate_raw_image


def home(request):
    now = timezone.now()
    
    # Фільтруємо турніри згідно з моделлю
    context = {
        'reg_open': Tournament.objects.filter(reg_start__lte=now, reg_end__gte=now),
        'running': Tournament.objects.filter(start_time__lte=now, end_time__gte=now),
        'finished': Tournament.objects.filter(end_time__lt=now),
        'upcoming': Tournament.objects.filter(reg_start__gt=now),
    }
    return render(request, 'home.html', context)

def index(request):
    now = timezone.now()
    
    # Використовуємо фільтри для різних категорій
    reg_open = Tournament.objects.filter(reg_start__lte=now, reg_end__gte=now)
    running = Tournament.objects.filter(start_time__lte=now, end_time__gte=now)
    finished = Tournament.objects.filter(end_time__lt=now)
    
    context = {
        'reg_open': reg_open,
        'running': running,
        'finished': finished,
        'now': now
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
        user.save()
        messages.success(request, 'Email підтверджено!')
        return redirect('login')
    else:
        messages.error(request, 'Посилання недійсне або застаріле.')
        return redirect('home')

def logout_view(request):
    django_logout(request)
    messages.success(request, 'Ви успішно вийшли з акаунта.')
    return redirect('home')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            link = request.build_absolute_uri(f'/verify/{uid}/{token}/')

            send_mail(
                subject='Підтвердіть вашу реєстрацію',
                message=f'Вітаємо, {user.nickname}!\n\nДля підтвердження email перейдіть за посиланням:\n{link}\n\nПосилання дійсне 24 години.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
            messages.success(request, 'На вашу пошту надіслано листа з підтвердженням.')
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})


def tournament_list(request):
    tournaments = Tournament.objects.all().order_by('-created_at', '-id')
    return render(request, 'tournaments/tournament_list.html', {'tournaments': tournaments})


def tournament_detail(request, tournament_id):
    # Використовуємо id=tournament_id, як передано в аргументах
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    # Оптимізуємо запит до команд, щоб не було проблем з капітанами
    teams = tournament.teams.all().select_related('captain')
    rounds = tournament.rounds.all()
    
    user_team = None
    if request.user.is_authenticated:
        # Перевіряємо, чи є юзер капітаном
        user_team = Team.objects.filter(tournament=tournament, captain=request.user).first()
        
        # Якщо не капітан, перевіряємо, чи є він учасником через модель TeamMember
        if not user_team:
            user_team = Team.objects.filter(
                tournament=tournament, 
                members__user=request.user # звертаємось через related_name або модель TeamMember
            ).first()

    return render(request, 'tournaments/tournament_detail.html', { 
        'tournament': tournament,
        'teams': teams,
        'rounds': rounds,
        'user_team': user_team,
    })

# У views.py для сторінки керування користувачами
def user_management(request):
    if request.user.role == UserRole.ORGANIZER:
        # Організатор бачить усіх
        users = User.objects.all()
    elif request.user.role == UserRole.ADMIN:
        # Адмін бачить тільки "простих смертних"
        users = User.objects.filter(role=UserRole.PARTICIPANT)
    else:
        return redirect('home')
    
    return render(request, 'management/users.html', {'users': users})

@login_required
def dashboard(request):
    user = request.user
    context = {
        'role': user.role,
        'nickname': user.nickname,
    }

    # 1. АДМІНІСТРАТОР
    if user.role == UserRole.ADMIN:
        context['total_users'] = User.objects.count()
        context['tournaments'] = Tournament.objects.all().annotate(teams_count=Count('teams'))
        return render(request, 'dashboards/admin_dashboard.html', context)

    # 2. ОРГАНІЗАТОР
    elif user.role == UserRole.ORGANIZER:
        context['my_tournaments'] = Tournament.objects.filter(creator=user).annotate(teams_count=Count('teams'))
        return render(request, 'dashboards/organizer_dashboard.html', context)

    # 3. ЖУРІ
    elif user.role == UserRole.JURY:
        context['my_evaluations'] = Evaluation.objects.filter(jury=user).select_related('submission__team', 'submission__round')
        return render(request, 'dashboards/jury_dashboard.html', context)

    # 4. УЧАСНИК
    elif user.role == UserRole.PARTICIPANT:
        # Шукаємо команду, де поточний юзер є капітаном
        team = Team.objects.filter(captain=user).select_related('tournament').first()
        
        if team:
            context.update({
                'team': team,
                'members': team.members.all(),
                'submissions': Submission.objects.filter(team=team).select_related('round').order_by('-created_at'),
                'form': SubmissionForm(team=team)
            })
            return render(request, 'dashboards/team_dashboard.html', context)
        else:
            # Якщо команди немає, замість редіректу покажемо пустий кабінет з пропозицією створити
            context['team'] = None
            return render(request, 'dashboards/team_dashboard.html', context)

    else:
        messages.error(request, 'Невідома роль користувача.')
        return redirect('home')
    
@login_required
def team_detail(request, pk):
    team = get_object_or_404(Team.objects.select_related('captain', 'tournament'), pk=pk)

    members = TeamMember.objects.filter(team=team).order_by('full_name')
    submissions = Submission.objects.filter(team=team).select_related('round').prefetch_related('evaluations').order_by('-created_at')
    
    # Перевіряємо, чи користувач є капітаном команди
    is_captain = team.captain == request.user

    return render(
        request,
        'tournaments/team_detail.html',
        {
            'team': team,
            'members': members,
            'submissions': submissions,
            'is_captain': is_captain,
        },
    )

@login_required
def create_team(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)

    # Перевірка статусу
    if tournament.status != TournamentStatus.REGISTRATION:
        messages.error(request, "Реєстрація на цей турнір наразі закрита.")
        return redirect('tournament_detail', tournament_id=tournament_id)

    # Перевірка вікна реєстрації
    now = timezone.now()
    if not (tournament.reg_start <= now <= tournament.reg_end):
        messages.error(request, "Реєстраційне вікно ще не відкрито або вже закрито.")
        return redirect('tournament_detail', tournament_id=tournament_id)

    if Team.objects.filter(captain=request.user).exists():
        messages.warning(request, "У вас вже є створена команда.")
        return redirect('home')

    if request.method == 'POST':
        team_name = request.POST.get('team_name', '').strip()
        if team_name:
            new_team = Team.objects.create(
                name=team_name,
                captain=request.user,
                tournament=tournament,
            )
            messages.success(request, f"Команду '{team_name}' успішно створено!")
            return redirect('team_dashboard')
    return render(request, 'tournaments/create_team.html', {'tournament': tournament})

@login_required
def register_for_tournament(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    user = request.user
    now = timezone.now()
    # Перевірка ролі
    if user.role != UserRole.PARTICIPANT:
        messages.error(request, "Тільки зареєстровані учасники можуть реєструвати команди.")
        return redirect('home')

    # Перевірка дедлайну реєстрації
    if now < tournament.reg_start:
        messages.error(request, "Реєстрація на цей турнір ще не відкрита.")
        return redirect('tournament_detail', tournament_id=tournament_id)
    if now > tournament.reg_end:
        messages.error(request, "Реєстрація на цей турнір уже закрита.")
        return redirect('tournament_detail', tournament_id=tournament_id)
    
    # Чи вже є у капітана команда?
    if Team.objects.filter(captain=user).exists():
        # Якщо команда вже є, просто прив'язуємо її до цього турніру (якщо вона ще не там)
        team = Team.objects.get(captain=user)
        if team.tournament == tournament:
            messages.info(request, "Ви вже зареєстровані на цей турнір.")
        else:
            messages.warning(request, "У вас уже є команда в іншому турнірі.")
        return redirect('team_dashboard')
    # Якщо все ок — відправляємо на створення команди
    return redirect('create_team', tournament_id=tournament.id)


@login_required
def team_dashboard(request):
    # Шукаємо команду, де поточний юзер є капітаном
    team = Team.objects.filter(captain=request.user).first()
    
    if not team:
        messages.info(request, "Ви ще не створили команду.")
        return redirect('home')
        
    return render(request, 'tournaments/team_dashboard.html', {'team': team})

@login_required
def submission_create(request, team_id):
    team = get_object_or_404(Team.objects.select_related('tournament', 'captain'), pk=team_id)

    if team.captain != request.user and not request.user.is_staff:
        messages.error(request, 'У вас немає доступу до подачі за цю команду.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = SubmissionForm(request.POST, team=team)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.team = team
            submission.save()
            messages.success(request, 'Роботу успішно подано.')
            return redirect('team_detail', pk=team.id)
    else:
        form = SubmissionForm(team=team)

    return render(request, 'tournaments/submission_form.html', {'form': form, 'team': team})

@login_required
def create_staff(request):
    if request.user.role not in [UserRole.ORGANIZER, UserRole.ADMIN]:
        messages.error(request, 'Доступ заборонено.')
        return redirect('dashboard')

    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip().lower()
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

# tournaments/views.py

@login_required
def tournament_dashboard(request):
    # Шукаємо команду, де користувач є капітаном
    managed_team = Team.objects.filter(captain=request.user).first()
    # Шукаємо команду, де користувач є звичайним учасником
    joined_team = Team.objects.filter(members=request.user).first()
    
    # Отримуємо список доступних турнірів для запису
    available_tournaments = Tournament.objects.all().order_by('-created_at')

    context = {
        'managed_team': managed_team,
        'joined_team': joined_team,
        'available_tournaments': available_tournaments,
    }
    return render(request, 'tournaments/dashboard.html', context)

def tournament_detail(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    # Перевіряємо, чи користувач уже в команді на цей турнір
    user_team = Team.objects.filter(tournament=tournament, members=request.user).first() or \
                Team.objects.filter(tournament=tournament, captain=request.user).first()
    
    # Отримуємо команди та раунди турніру
    teams = Team.objects.filter(tournament=tournament).select_related('captain')
    rounds = Round.objects.filter(tournament=tournament).order_by('start_time')
    
    return render(request, 'tournaments/tournament_detail.html', {
        'tournament': tournament,
        'user_team': user_team,
        'teams': teams,
        'rounds': rounds,
    })

@login_required
def add_team_member(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    
    if team.captain != request.user:
        messages.error(request, "Тільки капітан може додавати учасників.")
        return redirect('team_detail', pk=team_id)

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        
        # 1. Перевіряємо, чи існує користувач з таким email в системі
        user_to_add = User.objects.filter(email__iexact=email).first()
        
        if not user_to_add:
            messages.error(request, f"Користувача з email {email} не знайдено. Він має спочатку зареєструватися на платформі.")
            return redirect('team_detail', pk=team_id)

        # 2. Перевіряємо, чи він уже не в цій команді
        if TeamMember.objects.filter(team=team, user=user_to_add).exists():
            messages.warning(request, "Цей учасник вже є у вашій команді.")
            return redirect('team_detail', pk=team_id)

        # 3. Додаємо учасника
        TeamMember.objects.create(
            team=team,
            user=user_to_add,
            email=user_to_add.email,
            full_name=user_to_add.full_name # ПІБ підтягується автоматично з профілю
        )
        
        messages.success(request, f"Учасника {user_to_add.full_name} додано!")
        return redirect('team_detail', pk=team_id)

    return render(request, 'tournaments/add_member.html', {'team': team})

@login_required
def tournament_create(request):
    if request.user.role != UserRole.ADMIN:
        messages.error(request, "Доступ заборонено")
        return redirect('home')
    
    if request.method == 'POST':
        form = TournamentForm(request.POST, request.FILES)
        if form.is_valid():
            tournament = form.save(commit=False)
            tournament.creator = request.user
            tournament.save()
            messages.success(request, f"Турнір '{tournament.title}' створено!")
            return redirect('dashboard')
    else:
        form = TournamentForm()
    
    return render(request, 'tournaments/tournament_form.html', {
        'form': form, 
        'title': 'Створення турніру'
    })

@login_required
def tournament_edit(request, pk):
    if request.user.role != UserRole.ADMIN:
        return redirect('home')
    
    tournament = get_object_or_404(Tournament, pk=pk)
    if request.method == 'POST':
        form = TournamentForm(request.POST, request.FILES, instance=tournament)
        if form.is_valid():
            form.save()
            messages.success(request, "Параметри турніру оновлено")
            return redirect('dashboard')
    else:
        form = TournamentForm(instance=tournament)
    
    return render(request, 'tournaments/tournament_form.html', {
        'form': form, 
        'title': 'Редагування турніру',
        'tournament': tournament
    })

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
        submissions = list(Submission.objects.filter(round=round_obj))
        jury_members = list(User.objects.filter(role=UserRole.JURY))
        if not jury_members:
            return Response({'detail': 'Немає зареєстрованих членів журі'}, status=status.HTTP_400_BAD_REQUEST)
        created = 0
        for submission in submissions:
            chosen = random.sample(jury_members, k=min(2, len(jury_members)))
            for jury in chosen:
                _, was_created = Evaluation.objects.get_or_create(
                    submission=submission,
                    jury=jury,
                    defaults={'tech_score': 0, 'func_score': 0},
                )
                created += int(was_created)
        return Response({'status': 'Роботи розподілено між журі', 'created_assignments': created})


class SubmissionCreateView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def post(self, request):
        serializer = SubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()
        return Response(serializer.to_representation(submission), status=status.HTTP_201_CREATED)
