from django.db import migrations, models


def merge_roles(apps, schema_editor):
    User = apps.get_model("tournaments", "User")
    User.objects.filter(role__in=["player", "captain"]).update(role="participant")


class Migration(migrations.Migration):

    dependencies = [
        ("tournaments", "0006_restore_tournament_creator_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("admin", "Адміністратор"),
                    ("organizer", "Організатор"),
                    ("jury", "Журі"),
                    ("participant", "Учасник"),
                ],
                default="participant",
            ),
        ),
        migrations.RunPython(merge_roles, migrations.RunPython.noop),
    ]
