# Generated by Django 5.0.11 on 2025-04-08 17:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("thoughtswap", "0005_alter_channel_participants"),
    ]

    operations = [
        migrations.AddField(
            model_name="channel",
            name="channel_name",
            field=models.CharField(default="New Channel", max_length=255),
        ),
    ]
