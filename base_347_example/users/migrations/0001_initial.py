import django.contrib.auth.models
import django.contrib.auth.validators
import django.utils.timezone
from django.db import migrations
from django.db import models

import base_347_example.users.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login",
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),(
                    "username",
                    models.CharField(
                        error_messages={
                            "unique": "A user with that username already exists."
                        },
                        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                        max_length=150,
                        unique=True,
                        validators=[
                            django.contrib.auth.validators.UnicodeUsernameValidator()
                        ],
                        verbose_name="username",
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True, max_length=254, verbose_name="email address",
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="Name of User",
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.Group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.Permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "abstract": False,
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
    ]

def _update_or_create_site_with_sequence(site_model, connection, domain, name):
    """Update or create the site with default ID and keep the DB sequence in sync."""
    site, created = site_model.objects.update_or_create(
        id=settings.SITE_ID,
        defaults={
            "domain": domain,
            "name": name,
        },
    )
    if created:
        # We provided the ID explicitly when creating the Site entry, therefore the DB
        # sequence to auto-generate IDs wasn't used and is now out of sync. If we
        # don't do anything, we'll get a unique constraint violation the next time a
        # site is created.
        # To avoid this, we need to manually update DB sequence and make sure it's
        # greater than the maximum value.
        max_id = site_model.objects.order_by('-id').first().id

        with connection.cursor() as cursor:
            if connection.vendor == "postgresql":
                cursor.execute("SELECT last_value from django_site_id_seq")
                (current_id,) = cursor.fetchone()
                if current_id <= max_id:
                    cursor.execute(
                        "ALTER SEQUENCE django_site_id_seq RESTART WITH %s",
                        [max_id + 1],
                    )
            elif connection.vendor == "sqlite":
                cursor.execute("SELECT MAX(id) FROM django_site")
                current_id = cursor.fetchone()[0] or 0
                if current_id <= max_id:
                    try:
                        cursor.execute("INSERT INTO django_site (id, domain, name) VALUES (?, 'temp', 'temp')",
                                       (max_id + 1,))
                    except Exception:
                        pass
                    finally:
                        cursor.execute("DELETE FROM django_site WHERE domain='temp' AND name='temp'")
