from django.core.management.base import BaseCommand
from tournaments.models import User, UserRole

class Command(BaseCommand):
    help = 'Створює початкового Організатора'

    def handle(self, *args, **options):
        email = 'organizer@techcup.ua'
        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(
                email=email,
                password='Admin123!', # Потім зміните через "очко"
                nickname='TechCup Organizer',
                role=UserRole.ORGANIZER,
                is_verified=True
            )
            self.stdout.write(self.style.SUCCESS(f'Організатор {email} створений'))
        else:
            self.stdout.write(self.style.WARNING('Організатор уже існує'))