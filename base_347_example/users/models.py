from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, ManyToManyField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Group


class User(AbstractUser):
    """
    Default custom user model for Base 347 Example.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    CHOICES = [
        ("", ""),
        ("facilitator", "Facilitator"),
        ("participant", "Participant"),
    ]
    user_type = CharField(max_length=11, choices = CHOICES, default="no role")
    saved_posts = ManyToManyField('thoughtswap.Post', related_name='saved_by', blank=True)
    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})
