# Generated migration for tournament+captain uniqueness

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0013_team_organization'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='team',
            unique_together={('tournament', 'name'), ('tournament', 'captain')},
        ),
    ]
