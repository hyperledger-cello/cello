from django.contrib.auth.models import AbstractUser
from django.db import models

from api.models import Organization
from common.utils import make_uuid
from enums import UserRole


# Create your models here.

class UserProfile(AbstractUser):
    id = models.UUIDField(
        primary_key=True,
        help_text="ID of user",
        default=make_uuid,
        editable=True,
    )
    email = models.EmailField(db_index=True, unique=True)
    role = models.CharField(
        choices=UserRole.to_choices(string_as_value=True),
        default=UserRole.User.value,
        max_length=64,
        help_text=UserRole.get_info("User roles:", list_str=True),
    )
    organization = models.ForeignKey(
        Organization,
        null=True,
        on_delete=models.CASCADE,
        related_name="users",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "User Info"
        verbose_name_plural = verbose_name
        ordering = ["-date_joined"]

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.role == UserRole.Admin.name.lower()

    @property
    def is_operator(self):
        return self.role == UserRole.Operator.name.lower()

    @property
    def is_common_user(self):
        return self.role == UserRole.User.name.lower()
