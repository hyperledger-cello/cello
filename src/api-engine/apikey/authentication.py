#
# SPDX-License-Identifier: Apache-2.0
#
from hmac import compare_digest

from django.utils import timezone
from rest_framework.authentication import (
    BaseAuthentication,
    get_authorization_header,
)
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.permissions import SAFE_METHODS

from apikey.models import ApiKey, hash_secret


class APIKeyAuthentication(BaseAuthentication):
    """Authenticate with `Authorization: Api-Key <prefix>.<secret>`.

    Other schemes (e.g. Bearer) are ignored so JWT keeps working. The key's
    scope is enforced here, so no view can skip it.
    """

    keyword = "Api-Key"

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts or parts[0].lower() != self.keyword.lower().encode():
            return None
        if len(parts) != 2:
            raise AuthenticationFailed("Invalid API key header.")
        try:
            raw = parts[1].decode()
        except UnicodeError:
            raise AuthenticationFailed("Invalid API key header.")

        prefix, sep, secret = raw.partition(".")
        if not sep or not secret:
            raise AuthenticationFailed("Invalid API key.")
        try:
            key = ApiKey.objects.select_related("user").get(prefix=prefix)
        except ApiKey.DoesNotExist:
            raise AuthenticationFailed("Invalid API key.")

        if not compare_digest(key.key_hash, hash_secret(secret)):
            raise AuthenticationFailed("Invalid API key.")
        if key.revoked_at is not None:
            raise AuthenticationFailed("API key has been revoked.")
        if key.expires_at <= timezone.now():
            raise AuthenticationFailed("API key has expired.")
        if not key.user.is_active:
            raise AuthenticationFailed("User is inactive.")
        if (
            key.scope == ApiKey.Scope.READ
            and request.method not in SAFE_METHODS
        ):
            raise PermissionDenied("This API key is read-only.")

        ApiKey.objects.filter(pk=key.pk).update(last_used_at=timezone.now())
        return key.user, key

    def authenticate_header(self, request):
        return self.keyword
