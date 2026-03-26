#не працює
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from tournaments.models import Tournament, TournamentStatus, User, UserRole


class Command(BaseCommand):
    help = 'Seed demo data'

    def handle(self, *args, **options):
        organizer, _ = User.objects.get_or_create(
            email='organizer@example.com',
            defaults={'nickname': 'organizer', 'role': UserRole.ORGANIZER},
        )
        if not organizer.password:
            organizer.set_password('Organizer123!')
            organizer.save(update_fields=['password'])
        Tournament.objects.get_or_create(
            title='Demo Tournament 2026',
            defaults={
                'description': 'Seeded tournament',
                'status': TournamentStatus.REGISTRATION,
                'creator': organizer,
                'reg_start': timezone.now() - timedelta(days=1),
                'reg_end': timezone.now() + timedelta(days=7),
                'max_teams': 16,
            },
        )
        self.stdout.write(self.style.SUCCESS('Seed data ready'))
