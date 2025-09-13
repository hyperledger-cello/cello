from django.contrib.auth.models import AbstractUser
from django.db import models

from common.utils import make_uuid
from organization.models import Organization


# Create your models here.

class UserProfile(AbstractUser):
    class Role(models.TextChoices):
            ADMIN = "ADMIN", "Admin"
            USER = "USER", "User"

    id = models.UUIDField(
        primary_key=True,
        help_text="User ID",
        default=make_uuid,
    )
    email = models.EmailField(db_index=True, unique=True)
    role = models.CharField(
        choices=Role.choices,
        default=Role.USER,
        max_length=64,
        help_text="User Role",
    )
    organization = models.ForeignKey(
        Organization,
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
        return self.role == self.Role.ADMIN

    @property
    def is_common_user(self):
        return self.role == self.Role.USER
