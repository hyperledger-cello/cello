#
# SPDX-License-Identifier: Apache-2.0
#
import hashlib
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone

from common.utils import make_uuid


def hash_secret(secret):
    return hashlib.sha256(secret.encode()).hexdigest()


class ApiKey(models.Model):
    class Scope(models.TextChoices):
        READ = "read", "Read"
        WRITE = "write", "Write"

    id = models.UUIDField(
        primary_key=True,
        help_text="API key ID",
        default=make_uuid,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="api_keys",
    )
    name = models.CharField(max_length=64, help_text="Key label")
    prefix = models.CharField(max_length=16, unique=True)
    key_hash = models.CharField(max_length=64)
    scope = models.CharField(
        choices=Scope.choices,
        default=Scope.READ,
        max_length=16,
    )
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.prefix})"

    @property
    def is_active(self):
        return self.revoked_at is None and self.expires_at > timezone.now()

    @classmethod
    def issue(cls, user, name, scope, expires_at):
        """Create a key and return (instance, plaintext key).

        Only the SHA-256 hash of the secret is stored, so the plaintext
        cannot be recovered later.
        """
        prefix = secrets.token_hex(6)
        while cls.objects.filter(prefix=prefix).exists():
            prefix = secrets.token_hex(6)
        secret = secrets.token_urlsafe(32)
        key = cls.objects.create(
            user=user,
            name=name,
            prefix=prefix,
            key_hash=hash_secret(secret),
            scope=scope,
            expires_at=expires_at,
        )
        return key, f"{prefix}.{secret}"
