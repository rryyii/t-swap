# Generated by Django 5.0.11 on 2025-04-08 17:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("thoughtswap", "0004_alter_channel_posts_alter_post_responses"),
    ]

    operations = [
        migrations.AlterField(
            model_name="channel",
            name="participants",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="thoughtswap.participant",
            ),
        ),
    ]
