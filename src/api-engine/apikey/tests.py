#
# SPDX-License-Identifier: Apache-2.0
#
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apikey.models import ApiKey
from organization.models import Organization
from user.models import UserProfile

KEYS = "/api/v1/api-keys"
USERS = "/api/v1/users"


class ApiKeyTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = self.make_user("one")

    def make_user(self, tag):
        org = Organization.objects.create(
            name=f"{tag}.example.com",
            agent_url=f"http://agent-{tag}:8080/api/v1/",
            msp_id=f"{tag.capitalize()}MSP",
        )
        return UserProfile.objects.create_user(
            username=tag,
            email=f"{tag}@example.com",
            password="pw12345!",
            organization=org,
        )

    def jwt(self, user=None):
        token = RefreshToken.for_user(user or self.user).access_token
        return {"HTTP_AUTHORIZATION": f"JWT {token}"}

    def issue(self, scope=ApiKey.Scope.READ, days=30, user=None):
        key, raw = ApiKey.issue(
            user=user or self.user,
            name="test",
            scope=scope,
            expires_at=timezone.now() + timedelta(days=days),
        )
        return key, {"HTTP_AUTHORIZATION": f"Api-Key {raw}"}

    # authentication

    def test_valid_key_authenticates(self):
        _, auth = self.issue()
        self.assertEqual(self.client.get(USERS, **auth).status_code, 200)

    def test_jwt_still_works(self):
        res = self.client.get(USERS, **self.jwt())
        self.assertEqual(res.status_code, 200)

    def test_wrong_secret_rejected(self):
        key, _ = self.issue()
        auth = {"HTTP_AUTHORIZATION": f"Api-Key {key.prefix}.wrong"}
        self.assertEqual(self.client.get(USERS, **auth).status_code, 401)

    def test_malformed_key_rejected(self):
        auth = {"HTTP_AUTHORIZATION": "Api-Key nodothere"}
        self.assertEqual(self.client.get(USERS, **auth).status_code, 401)

    def test_expired_key_rejected(self):
        _, auth = self.issue(days=-1)
        self.assertEqual(self.client.get(USERS, **auth).status_code, 401)

    def test_revoked_key_rejected(self):
        key, auth = self.issue()
        key.revoked_at = timezone.now()
        key.save()
        self.assertEqual(self.client.get(USERS, **auth).status_code, 401)

    def test_inactive_user_rejected(self):
        _, auth = self.issue()
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.client.get(USERS, **auth).status_code, 401)

    def test_last_used_is_updated(self):
        key, auth = self.issue()
        self.assertIsNone(key.last_used_at)
        self.client.get(USERS, **auth)
        key.refresh_from_db()
        self.assertIsNotNone(key.last_used_at)

    # scope

    def test_read_key_blocked_on_unsafe_methods(self):
        _, auth = self.issue(scope=ApiKey.Scope.READ)
        self.assertEqual(self.client.post(USERS, {}, **auth).status_code, 403)
        self.assertEqual(self.client.put(USERS, {}, **auth).status_code, 403)
        self.assertEqual(self.client.delete(USERS, **auth).status_code, 403)

    def test_read_scope_applies_on_any_endpoint(self):
        _, auth = self.issue(scope=ApiKey.Scope.READ)
        res = self.client.post("/api/v1/channels", {}, **auth)
        self.assertEqual(res.status_code, 403)

    # key management

    def test_create_returns_plaintext_once(self):
        res = self.client.post(KEYS, {"name": "mcp"}, **self.jwt())
        self.assertEqual(res.status_code, 201)
        self.assertIn("key", res.data)
        self.assertEqual(res.data["scope"], "read")
        self.assertNotIn("key_hash", res.data)
        listed = self.client.get(KEYS, **self.jwt())
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.data), 1)
        self.assertNotIn("key", listed.data[0])
        self.assertNotIn("key_hash", listed.data[0])

    def test_created_key_works(self):
        res = self.client.post(KEYS, {"name": "mcp"}, **self.jwt())
        auth = {"HTTP_AUTHORIZATION": f"Api-Key {res.data['key']}"}
        self.assertEqual(self.client.get(USERS, **auth).status_code, 200)

    def test_plaintext_is_not_stored(self):
        res = self.client.post(KEYS, {"name": "mcp"}, **self.jwt())
        secret = res.data["key"].split(".", 1)[1]
        key = ApiKey.objects.get(pk=res.data["id"])
        self.assertNotIn(secret, key.key_hash)
        self.assertEqual(len(key.key_hash), 64)

    def test_expiry_is_validated(self):
        res = self.client.post(
            KEYS, {"name": "x", "expires_in_days": 0}, **self.jwt()
        )
        self.assertEqual(res.status_code, 400)

    def test_revoke(self):
        key, auth = self.issue()
        res = self.client.post(f"{KEYS}/{key.id}/revoke", **self.jwt())
        self.assertEqual(res.status_code, 200)
        self.assertIsNotNone(res.data["revoked_at"])
        self.assertEqual(self.client.get(USERS, **auth).status_code, 401)

    def test_api_key_cannot_manage_keys(self):
        key, auth = self.issue()
        self.assertEqual(self.client.get(KEYS, **auth).status_code, 401)
        res = self.client.post(KEYS, {"name": "x"}, **auth)
        self.assertEqual(res.status_code, 401)
        res = self.client.post(f"{KEYS}/{key.id}/revoke", **auth)
        self.assertEqual(res.status_code, 401)

    def test_keys_are_private_to_their_owner(self):
        other = self.make_user("two")
        key, _ = self.issue(user=other)
        listed = self.client.get(KEYS, **self.jwt())
        self.assertEqual(listed.data, [])
        res = self.client.post(f"{KEYS}/{key.id}/revoke", **self.jwt())
        self.assertEqual(res.status_code, 404)
