from datetime import timedelta
import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from tournaments.models import Tournament, TournamentStatus, User, Team, TeamMember, UserRole, Round, Submission, Evaluation


class Command(BaseCommand):
    help = 'Seed demo data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')

        password = 'Admin123!'
        now = timezone.now()

        def ensure_user(email, nickname, role, full_name, discord_tag):
            user, _ = User.objects.get_or_create(
                email=email,
                defaults={
                    'nickname': nickname,
                    'role': role,
                    'full_name': full_name,
                    'discord_tag': discord_tag,
                    'is_verified': True,
                    'profile_image': None,
                },
            )
            user.set_password(password)
            user.save()
            return user

        # Organizer (NO ADMIN)
        organizer = ensure_user(
            email='organizer@gmail.com',
            nickname='organizer_user',
            role=UserRole.ORGANIZER,
            full_name='Організатор В',
            discord_tag='organizer#0002',
        )

        # 4 jury users
        juries_specs = [
            ('jury1@gmail.com', 'jury_user_1', 'Журі 1', 'jury1#0004'),
            ('jury2@gmail.com', 'jury_user_2', 'Журі 2', 'jury2#0005'),
            ('jury3@gmail.com', 'jury_user_3', 'Журі 3', 'jury3#0006'),
            ('jury4@gmail.com', 'jury_user_4', 'Журі 4', 'jury4#0007'),
        ]
        juries = [
            ensure_user(email, nickname, UserRole.JURY, full_name, discord_tag)
            for (email, nickname, full_name, discord_tag) in juries_specs
        ]

        # 6 participant users
        participants_specs = [
            ('participant1@gmail.com', 'participant1', 'Іван Капітан', 'ivan_captain#3001'),
            ('participant2@gmail.com', 'participant2', 'Петро Учасник', 'petro_member#3002'),
            ('participant3@gmail.com', 'participant3', 'Марія Учасник', 'maria_member#3003'),
            ('participant4@gmail.com', 'participant4', 'Олег Учасник', 'oleh_member#3004'),
            ('participant5@gmail.com', 'participant5', 'Анна Учасник', 'anna_member#3005'),
            ('participant6@gmail.com', 'participant6', 'Софія Учасник', 'sofiya_member#3006'),
        ]
        participants = [
            ensure_user(email, nickname, UserRole.PARTICIPANT, full_name, discord_tag)
            for (email, nickname, full_name, discord_tag) in participants_specs
        ]

        # === Create 3 tournaments, 2 teams each ===
        tournament_titles = [
            'Grantt Championship 2026 #1',
            'Grantt Championship 2026 #2',
            'Grantt Championship 2026 #3',
        ]

        created_tournaments = []
        for t_idx, title in enumerate(tournament_titles):
            tournament, _ = Tournament.objects.get_or_create(
                title=title,
                defaults={
                    'description': 'Seeded tournament.',
                    'status': TournamentStatus.REGISTRATION,
                    'creator': organizer,
                    'reg_start': now - timedelta(days=1),
                    'reg_end': now + timedelta(days=7),
                    'start_time': now + timedelta(days=8),
                    'end_time': now + timedelta(days=15),
                    'max_teams': 16,
                    'max_team_members': 5,
                    'min_team_members': 2,
                    'cover_image': None,
                },
            )

            created_tournaments.append(tournament)

            # Add all juries to every tournament (for predictable seeding)
            for jury in juries:
                jury.jury_tournaments.add(tournament)

            # 2 teams per tournament (6 teams total)
            p1 = participants[t_idx * 2]
            p2 = participants[t_idx * 2 + 1]

            team1, _ = Team.objects.get_or_create(
                tournament=tournament,
                name=f'Seed Spartans {t_idx + 1}',
                defaults={
                    'captain': p1,
                    'captain_email': p1.email.lower(),
                    'captain_name': p1.full_name,
                    'organization': f'Seed University{t_idx * 2 + 1}',
                },
            )
            team2, _ = Team.objects.get_or_create(
                tournament=tournament,
                name=f'Seed Warriors {t_idx + 1}',
                defaults={
                    'captain': p2,
                    'captain_email': p2.email.lower(),
                    'captain_name': p2.full_name,
                    'organization': f'Seed University{t_idx * 2 + 2}',
                },
            )

            # Create a sample team member (UI checks)  
            TeamMember.objects.get_or_create(
                team=team1,
                email=p2.email.lower(),
                defaults={
                    'full_name': p2.full_name,
                    'user': p2,
                },
            )
            TeamMember.objects.get_or_create(
                team=team2,
                email=p1.email.lower(),
                defaults={
                    'full_name': p1.full_name,
                    'user': p1,
                },
            )

            # Round
            round1, _ = Round.objects.get_or_create(
                tournament=tournament,
                title='Round 1',
                defaults={
                    'description': 'Description of Round 1',
                    'requirements': 'Requirements of Round 1',
                    'start_time': now - timedelta(days=1),
                    'end_time': now + timedelta(days=1),
                    'status': 'Draft',
                },
            )
            round1.save()
            round1.set_scoring_criteria([
                {'name': 'Technical', 'max_score': 100},
                {'name': 'Functionality', 'max_score': 100},
            ])

            # Submissions for each team
            submissions = []
            for (team, label) in [(team1, '1'), (team2, '2')]:
                submission, _ = Submission.objects.get_or_create(
                    team=team,
                    round=round1,
                    defaults={
                        'github_link': f'https://github.com/example/submission-{t_idx + 1}-{label}',
                        'video_link': f'https://www.youtube.com/watch?v=example{t_idx + 1}{label}',
                        'description': f'Description of Submission {t_idx + 1}-{label}',
                    },
                )
                submission.save()
                submissions.append(submission)

            # Distribute works to jury: create Evaluation rows (one jury per submission)
            jury_members = list(User.objects.filter(role=UserRole.JURY, jury_tournaments=tournament))
            if jury_members:
                for s_idx, submission in enumerate(submissions):
                    chosen_jury = random.choice(jury_members)
                    evaluation, _ = Evaluation.objects.get_or_create(
                        submission=submission,
                        defaults={
                            'jury': chosen_jury,
                        },
                    )
                    evaluation.ensure_score_entries()

                    # No null score - only for first tournament and first submission
                    if t_idx == 0 and s_idx == 0:
                        evaluation = Evaluation.objects.get(submission=submission)
                        score_map = {'Technical': 80, 'Functionality': 70}
                        for item in evaluation.ensure_score_entries():
                            item.score = score_map.get(item.criterion.name, 0)
                            item.save(update_fields=['score'])

            # === FOR TOURNAMENT #3: Add a second round with different criteria ===
            if t_idx == 2:
                round2, _ = Round.objects.get_or_create(
                    tournament=tournament,
                    title='Round 2 - Final',
                    defaults={
                        'description': 'Final Round - Advanced Features',
                        'requirements': 'Implement advanced features and optimizations',
                        'start_time': now - timedelta(days=1),
                        'end_time': now - timedelta(hours=1),  # Finished
                        'status': 'closed',
                    },
                )
                round2.save()
                round2.set_scoring_criteria([
                    {'name': 'Code Quality', 'max_score': 100},
                    {'name': 'Innovation', 'max_score': 100},
                    {'name': 'Performance', 'max_score': 100},
                ])

                # Submissions for round 2
                round2_submissions = []
                for (team, label) in [(team1, '1'), (team2, '2')]:
                    submission, _ = Submission.objects.get_or_create(
                        team=team,
                        round=round2,
                        defaults={
                            'github_link': f'https://github.com/example/final-submission-{t_idx + 1}-{label}',
                            'video_link': f'https://www.youtube.com/watch?v=final{t_idx + 1}{label}',
                            'description': f'Final Submission {t_idx + 1}-{label} with advanced features',
                        },
                    )
                    submission.save()
                    round2_submissions.append(submission)

                # Evaluate round 2 submissions with scores
                if jury_members:
                    for s_idx, submission in enumerate(round2_submissions):
                        chosen_jury = random.choice(jury_members)
                        evaluation, _ = Evaluation.objects.get_or_create(
                            submission=submission,
                            defaults={
                                'jury': chosen_jury,
                            },
                        )
                        evaluation.ensure_score_entries()
                        
                        # Add scores for round 2
                        evaluation = Evaluation.objects.get(submission=submission)
                        score_map = {
                            'Code Quality': 85 + (s_idx * 5),
                            'Innovation': 75 + (s_idx * 8),
                            'Performance': 90 + (s_idx * 3),
                        }
                        for item in evaluation.ensure_score_entries():
                            item.score = score_map.get(item.criterion.name, 0)
                            item.save(update_fields=['score'])

        # === Final message ===
        self.stdout.write(self.style.SUCCESS('Seed data created successfully!'))
        self.stdout.write(self.style.WARNING('Created/ensured:'))
        self.stdout.write(f'  Organizer: organizer@gmail.com / {password}')
        self.stdout.write('  Jurys:')
        for idx, spec in enumerate(juries_specs, start=1):
            self.stdout.write(f'    Jury {idx}: {spec[0]} / {password}')
        self.stdout.write('  Participants:')
        for idx, spec in enumerate(participants_specs, start=1):
            self.stdout.write(f'    Participant {idx}: {spec[0]} / {password}')

        self.stdout.write('\n  Tournaments:')
        for idx, t in enumerate(created_tournaments, start=1):
            teams = list(Team.objects.filter(tournament=t).values_list('name', flat=True))
            rounds_count = t.rounds.count()
            extra_note = ' ⭐ (Completed leaderboard with 2 rounds!)' if idx == 3 else ''
            self.stdout.write(f'    {t.title} | Teams: {", ".join(teams)} | Rounds: {rounds_count}{extra_note}')
