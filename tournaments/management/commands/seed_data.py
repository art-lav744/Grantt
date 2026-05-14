from datetime import timedelta
from itertools import cycle

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from tournaments.models import (
    Evaluation,
    JuryRegistrationStatus,
    JuryTournamentRegistration,
    Round,
    RoundStatus,
    Submission,
    Team,
    TeamMember,
    Tournament,
    TournamentFile,
    TournamentStatus,
    User,
    UserRole,
)


PASSWORD = 'Admin123!'

ADMIN_EMAIL = 'admin@example.com'
ORGANIZER_EMAIL = 'organizer@techcup.ua'

JURY_SPECS = [
    ('jury1@gmail.com', 'jury_user_1', 'Журі 1', 'jury1#0001'),
    ('jury2@gmail.com', 'jury_user_2', 'Журі 2', 'jury2#0002'),
    ('jury3@gmail.com', 'jury_user_3', 'Журі 3', 'jury3#0003'),
]

PARTICIPANT_SPECS = [
    ('participant1@gmail.com', 'participant1', 'Іван Капітан', 'ivan#1001'),
    ('participant2@gmail.com', 'participant2', 'Петро Учасник', 'petro#1002'),
    ('participant3@gmail.com', 'participant3', 'Марія Капітан', 'maria#1003'),
    ('participant4@gmail.com', 'participant4', 'Олег Учасник', 'oleh#1004'),
    ('participant5@gmail.com', 'participant5', 'Анна Капітан', 'anna#1005'),
    ('participant6@gmail.com', 'participant6', 'Софія Учасник', 'sofia#1006'),
    ('participant7@gmail.com', 'participant7', 'Дмитро Капітан', 'dmytro#1007'),
    ('participant8@gmail.com', 'participant8', 'Назар Учасник', 'nazar#1008'),
    ('participant9@gmail.com', 'participant9', 'Олена Капітан', 'olena#1009'),
    ('participant10@gmail.com', 'participant10', 'Артем Учасник', 'artem#1010'),
    ('participant11@gmail.com', 'participant11', 'Юлія Капітан', 'julia#1011'),
    ('participant12@gmail.com', 'participant12', 'Максим Учасник', 'max#1012'),
]

TOURNAMENT_TITLES = [
    'Grantt Championship 2026 #1',
    'Grantt Championship 2026 #2',
    'Grantt Championship 2026 #3',
]


class Command(BaseCommand):
    help = 'Seed demo data that matches current backend validation rules.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        now = timezone.now()

        Tournament.objects.filter(title__in=TOURNAMENT_TITLES).delete()

        admin = self.ensure_user(
            email=ADMIN_EMAIL,
            nickname='admin',
            role=UserRole.ADMIN,
            full_name='Адміністратор Grantt',
            discord_tag='admin#0001',
            is_staff=True,
            is_superuser=True,
        )
        organizer = self.ensure_user(
            email=ORGANIZER_EMAIL,
            nickname='organizer',
            role=UserRole.ORGANIZER,
            full_name='Організатор Grantt',
            discord_tag='organizer#0001',
            is_staff=True,
        )
        juries = [
            self.ensure_user(email, nickname, UserRole.JURY, full_name, discord_tag)
            for email, nickname, full_name, discord_tag in JURY_SPECS
        ]
        participants = [
            self.ensure_user(email, nickname, UserRole.PARTICIPANT, full_name, discord_tag)
            for email, nickname, full_name, discord_tag in PARTICIPANT_SPECS
        ]

        tournaments = [
            self.create_registration_tournament(now, organizer),
            self.create_active_tournament(now, organizer),
            self.create_finished_tournament(now, organizer),
        ]

        participant_pairs = [participants[index:index + 2] for index in range(0, len(participants), 2)]
        for tournament_index, tournament in enumerate(tournaments):
            for jury in juries:
                jury.jury_tournaments.add(tournament)
                JuryTournamentRegistration.objects.create(
                    jury=jury,
                    tournament=tournament,
                    status=JuryRegistrationStatus.APPROVED,
                    reviewed_by=admin,
                    reviewed_at=now,
                )

            teams = []
            for team_index in range(2):
                captain, member = participant_pairs[tournament_index * 2 + team_index]
                team = self.create_team(
                    tournament=tournament,
                    captain=captain,
                    member=member,
                    name=f'Seed {"Spartans" if team_index == 0 else "Warriors"} {tournament_index + 1}',
                )
                teams.append(team)

            self.create_tournament_file(tournament, organizer, 'Регламент турніру', 'rules')
            self.create_tournament_file(tournament, organizer, 'Матеріали для учасників', 'general')

            if tournament_index == 0:
                self.create_round(
                    tournament=tournament,
                    title='Раунд 1 - Підготовка',
                    now=now,
                    status=RoundStatus.DRAFT,
                    start_offset=timedelta(days=8),
                    end_offset=timedelta(days=10),
                    criteria=[
                        {'name': 'Technical', 'max_score': 100},
                        {'name': 'Functionality', 'max_score': 100},
                    ],
                )
            elif tournament_index == 1:
                round_obj = self.create_round(
                    tournament=tournament,
                    title='Round 1',
                    now=now,
                    status=RoundStatus.ACTIVE,
                    start_offset=-timedelta(days=1),
                    end_offset=timedelta(days=2),
                    criteria=[
                        {'name': 'Technical', 'max_score': 100},
                        {'name': 'Functionality', 'max_score': 100},
                        {'name': 'Presentation', 'max_score': 50},
                    ],
                )
                self.create_submissions_and_evaluations(round_obj, teams, juries, score_sets=[
                    {'Technical': 82, 'Functionality': 76, 'Presentation': 44},
                    None,
                ])
            else:
                round_one = self.create_round(
                    tournament=tournament,
                    title='Round 1',
                    now=now,
                    status=RoundStatus.CLOSED,
                    start_offset=-timedelta(days=10),
                    end_offset=-timedelta(days=8),
                    criteria=[
                        {'name': 'Technical', 'max_score': 100},
                        {'name': 'Functionality', 'max_score': 100},
                    ],
                )
                round_two = self.create_round(
                    tournament=tournament,
                    title='Round 2 - Final',
                    now=now,
                    status=RoundStatus.CLOSED,
                    start_offset=-timedelta(days=7),
                    end_offset=-timedelta(days=5),
                    criteria=[
                        {'name': 'Code Quality', 'max_score': 100},
                        {'name': 'Innovation', 'max_score': 100},
                        {'name': 'Performance', 'max_score': 100},
                    ],
                )
                self.create_submissions_and_evaluations(round_one, teams, juries, score_sets=[
                    {'Technical': 88, 'Functionality': 84},
                    {'Technical': 79, 'Functionality': 91},
                ])
                self.create_submissions_and_evaluations(round_two, teams, juries, score_sets=[
                    {'Code Quality': 91, 'Innovation': 86, 'Performance': 90},
                    {'Code Quality': 84, 'Innovation': 95, 'Performance': 82},
                ])

        self.stdout.write(self.style.SUCCESS('Seed data created successfully.'))
        self.stdout.write(self.style.WARNING(f'Password for every seeded account: {PASSWORD}'))
        self.stdout.write(f'  Admin:      {ADMIN_EMAIL}')
        self.stdout.write(f'  Organizer:  {ORGANIZER_EMAIL}')
        for email, *_ in JURY_SPECS:
            self.stdout.write(f'  Jury:       {email}')
        for email, *_ in PARTICIPANT_SPECS:
            self.stdout.write(f'  Participant:{email}')

    def ensure_user(
        self,
        email,
        nickname,
        role,
        full_name,
        discord_tag,
        is_staff=False,
        is_superuser=False,
    ):
        user, _ = User.objects.get_or_create(email=email, defaults={'nickname': nickname})
        user.nickname = nickname
        user.role = role
        user.full_name = full_name
        user.discord_tag = discord_tag
        user.is_verified = True
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.set_password(PASSWORD)
        user.save()
        return user

    def create_registration_tournament(self, now, organizer):
        return Tournament.objects.create(
            title=TOURNAMENT_TITLES[0],
            description='Турнір відкритий для реєстрації команд.',
            status=TournamentStatus.REGISTRATION,
            creator=organizer,
            reg_start=now - timedelta(days=1),
            reg_end=now + timedelta(days=7),
            start_time=now + timedelta(days=8),
            end_time=now + timedelta(days=14),
            max_teams=16,
            min_team_members=2,
            max_team_members=5,
            max_rounds=2,
        )

    def create_active_tournament(self, now, organizer):
        return Tournament.objects.create(
            title=TOURNAMENT_TITLES[1],
            description='Активний турнір із поточним раундом і подачами робіт.',
            status=TournamentStatus.OPEN,
            creator=organizer,
            reg_start=now - timedelta(days=12),
            reg_end=now - timedelta(days=3),
            start_time=now - timedelta(days=2),
            end_time=now + timedelta(days=5),
            max_teams=16,
            min_team_members=2,
            max_team_members=5,
            max_rounds=2,
        )

    def create_finished_tournament(self, now, organizer):
        return Tournament.objects.create(
            title=TOURNAMENT_TITLES[2],
            description='Завершений турнір із готовою таблицею лідерів.',
            status=TournamentStatus.CLOSED,
            creator=organizer,
            reg_start=now - timedelta(days=20),
            reg_end=now - timedelta(days=15),
            start_time=now - timedelta(days=14),
            end_time=now - timedelta(days=1),
            max_teams=16,
            min_team_members=2,
            max_team_members=5,
            max_rounds=2,
        )

    def create_team(self, tournament, captain, member, name):
        team = Team.objects.create(
            tournament=tournament,
            name=name,
            captain=captain,
            captain_email=captain.email.lower(),
            captain_name=captain.full_name,
            organization='Grantt Demo School',
        )
        TeamMember.objects.create(
            team=team,
            email=member.email.lower(),
            full_name=member.full_name,
            user=member,
        )
        return team

    def create_round(self, tournament, title, now, status, start_offset, end_offset, criteria):
        round_obj = Round.objects.create(
            tournament=tournament,
            title=title,
            description=f'Демо-опис для {title}.',
            requirements='GitHub repo, demo video, short project description.',
            start_time=now + start_offset,
            end_time=now + end_offset,
            status=status,
        )
        round_obj.set_scoring_criteria(criteria)
        return round_obj

    def create_submissions_and_evaluations(self, round_obj, teams, juries, score_sets):
        jury_cycle = cycle(juries)
        for index, (team, score_map) in enumerate(zip(teams, score_sets), start=1):
            submission = Submission.objects.create(
                team=team,
                round=round_obj,
                github_link=f'https://github.com/grantt-demo/{team.name.lower().replace(" ", "-")}-{round_obj.id}',
                video_link=f'https://www.youtube.com/watch?v=demo{round_obj.id}{index}',
                description=f'Демо-робота команди {team.name} для {round_obj.title}.',
            )
            evaluation = Evaluation.objects.create(submission=submission, jury=next(jury_cycle))
            scores = evaluation.ensure_score_entries()
            if score_map is None:
                continue
            for score in scores:
                score.score = score_map.get(score.criterion.name, 0)
                score.save(update_fields=['score'])

    def create_tournament_file(self, tournament, uploaded_by, title, file_type):
        TournamentFile.objects.create(
            tournament=tournament,
            uploaded_by=uploaded_by,
            title=title,
            file_type=file_type,
            file=ContentFile(
                f'{title}\n{tournament.title}\nDemo file generated by seed_data.\n'.encode('utf-8'),
                name=f'{tournament.title.lower().replace(" ", "-")}-{file_type}.txt',
            ),
        )
