from django.core.management.base import BaseCommand
from tournaments.models import User, UserRole


class Command(BaseCommand):
    help = 'Create default admin user if missing'

    def handle(self, *args, **options):
        email = 'admin@example.com'
        password = 'Admin123!'
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING('Admin already exists'))
            return
        User.objects.create_superuser(email=email, password=password, nickname='admin', role=UserRole.ADMIN)
        self.stdout.write(self.style.SUCCESS(f'Created admin: {email} / {password}'))
