# Generated by Django 5.0.11 on 2025-04-08 20:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_user_user_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="user_type",
            field=models.CharField(
                choices=[
                    ("", ""),
                    ("facilitator", "Facilitator"),
                    ("participant", "Participant"),
                ],
                default="no role",
                max_length=11,
            ),
        ),
    ]
