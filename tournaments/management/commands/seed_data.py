#не працює
from datetime import timedelta
import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from tournaments.models import Tournament, TournamentStatus, User, Team, TeamMember, UserRole, Round, Submission, Evaluation


class Command(BaseCommand):
    help = 'Seed demo data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')

        # Admin User
        admin, _ = User.objects.get_or_create(
            email='admin@gmail.com',
            defaults={
                'nickname': 'admin_user',
                'role': UserRole.ADMIN,
                'full_name': 'Адміністратор В',
                'discord_tag': 'admin#0001',
                'is_verified': True,
                'profile_image': None,
            }
        )
        admin.set_password('Password123!')
        admin.save()
        # Organizer User
        organizer, _ = User.objects.get_or_create(
            email='organizer@gmail.com',
            defaults={
                'nickname': 'organizer_user',
                'role': UserRole.ORGANIZER,
                'full_name': 'Організатор В',
                'discord_tag': 'organizer#0002',
                'is_verified': True,
                'profile_image': None,
            }
        )
        organizer.set_password('Password123!')
        organizer.save()
        # Participant 1
        participant1, _ = User.objects.get_or_create(
            email='participant1@gmail.com',
            defaults={
                'nickname': 'captain_team1',
                'role': UserRole.PARTICIPANT,
                'full_name': 'Іван Капітан',
                'discord_tag': 'ivan_captain#3001',
                'is_verified': True,
                'profile_image': None,
            }
        )
        participant1.set_password('Password123!')
        participant1.save()

        # Participant 2
        participant2, _ = User.objects.get_or_create(
            email='participant2@gmail.com',
            defaults={
                'nickname': 'member_team1',
                'role': UserRole.PARTICIPANT,
                'full_name': 'Петро Учасник',
                'discord_tag': 'petro_member#3002',
                'is_verified': True,
                'profile_image': None,
            }
        )
        participant2.set_password('Password123!')
        participant2.save()

        # Participant 3
        participant3, _ = User.objects.get_or_create(
            email='participant3@gmail.com',
            defaults={
                'nickname': 'member_team2',
                'role': UserRole.PARTICIPANT,
                'full_name': 'Марія Учасник',
                'discord_tag': 'maria_member#3003',
                'is_verified': True,
                'profile_image': None,
            }
        )
        participant3.set_password('Password123!')
        participant3.save()

        # === CREATE TOURNAMENT ===
        
        tournament, _ = Tournament.objects.get_or_create(
            title='Grantt Championship 2026',
            defaults={
                'description': 'Seeded tournament.',
                'status': TournamentStatus.REGISTRATION,
                'creator': organizer,
                'reg_start': timezone.now() - timedelta(days=1),
                'reg_end': timezone.now() + timedelta(days=7),
                'start_time': timezone.now() + timedelta(days=8),
                'end_time': timezone.now() + timedelta(days=15),
                'max_teams': 16,
                'max_team_members': 5,
                'min_team_members': 2,
                'cover_image': None,
            }
        )
        
        # Jury User
        jury, _ = User.objects.get_or_create(
            email='jury@gmail.com',
            defaults={
                'nickname': 'jury_user',
                'role': UserRole.JURY,
                'full_name': 'Журі В',
                'discord_tag': 'jury#0004',
                'is_verified': True,
                'profile_image': None,
            }
        )
        jury.set_password('Password123!')
        jury.save()
        jury.jury_tournaments.add(tournament)
        
        # === CREATE TEAMS ===
        
        team1, _ = Team.objects.get_or_create(
            tournament=tournament,
            name='Seed Spartans',
            defaults={
                'captain': participant1,
                'captain_email': participant1.email.lower(),
                'captain_name': participant1.full_name,
                'organization': 'Seed University1',
            }
        )
        
        team2, _ = Team.objects.get_or_create(
            tournament=tournament,
            name='Seed Warriors',
            defaults={
                'captain': participant3,
                'captain_email': participant3.email.lower(),
                'captain_name': participant3.full_name,
                'organization': 'Seed University2',
            }
        )
        
        # === CREATE TEAM MEMBERS ===
        
        TeamMember.objects.get_or_create(
            team=team1,
            email=participant2.email.lower(),
            defaults={
                'full_name': participant2.full_name,
                'user': participant2,
            }
        )


        round1, _ = Round.objects.get_or_create(
            tournament=tournament,
            title='Round 1',
            description='Description of Round 1',
            requirements='Requirements of Round 1',
            start_time=timezone.now() - timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1),
            status='Draft',
        )
        round1.save()
        
        # === CREATE SUBMISSIONS ===
        submission1, _ = Submission.objects.get_or_create(
            team=team1,
            round=round1,
            github_link='https://github.com/example',
            video_link='https://www.youtube.com/watch?v=example',
            description='Description of Submission 1',
        )
        submission1.save()
        
        # Distribute works to jury
        submissions = list(Submission.objects.filter(round=round1))
        jury_members = list(User.objects.filter(role=UserRole.JURY, jury_tournaments=tournament))
        if jury_members:
            k_actual = min(3, len(jury_members))
            for submission in submissions:
                chosen = random.sample(jury_members, k=k_actual)
                for jury in chosen:
                    Evaluation.objects.get_or_create(
                        submission=submission,
                        jury=jury,
                        defaults={'tech_score': 0, 'func_score': 0},
                    )
        
        self.stdout.write(self.style.SUCCESS('  Seed data created successfully!'))
        self.stdout.write(self.style.WARNING('   Created:'))
        self.stdout.write(f'    Admin: admin@gmail.com / Password123!')
        self.stdout.write(f'    Organizer: organizer@gmail.com / Password123!')
        self.stdout.write(f'    Jury: jury@gmail.com / Password123!')
        self.stdout.write(f'    Participant 1: participant1@gmail.com / Password123!')
        self.stdout.write(f'    Participant 2: participant2@gmail.com / Password123!')
        self.stdout.write(f'    Participant 3: participant3@gmail.com / Password123!')
        self.stdout.write(f'\n   Tournament: {tournament.title}')
        self.stdout.write(f'    Status: {tournament.status}')
        self.stdout.write(f'    Reg Window: {tournament.reg_start} - {tournament.reg_end}')
        self.stdout.write(f'\n   Teams: {team1.name}, {team2.name}')
