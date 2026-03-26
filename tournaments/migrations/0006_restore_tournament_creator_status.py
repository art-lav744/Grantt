from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0005_alter_team_unique_together_team_members_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tournament',
            name='creator',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='tournaments',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='tournament',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft', 'Draft'),
                    ('registration', 'Registration'),
                    ('open', 'Open'),
                    ('closed', 'Closed'),
                    ('archived', 'Archived'),
                ],
                default='draft',
                max_length=20,
            ),
        ),
    ]
