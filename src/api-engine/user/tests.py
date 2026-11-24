from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from organization.models import Organization
from user.models import UserProfile
from user.views import UserViewSet


class UserDeleteTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.delete_user = UserViewSet.as_view({"delete": "destroy"})

        self.organization = Organization.objects.create(
            name="org-one",
            msp_id="OrgOneMSP",
        )
        self.other_organization = Organization.objects.create(
            name="org-two",
            msp_id="OrgTwoMSP",
        )
        self.request_user = self.create_user(
            "requester@example.com",
            self.organization,
        )

    def create_user(self, email, organization):
        user = UserProfile(
            username=email,
            email=email,
            organization=organization,
            role=UserProfile.Role.ADMIN,
        )
        user.set_password("test-password")
        user.save()
        return user

    def make_delete_request(self, user, target_id):
        request = self.factory.delete(f"/users/{target_id}")
        force_authenticate(request, user=user)
        return self.delete_user(request, pk=str(target_id))

    def test_user_can_delete_user_in_same_organization(self):
        target = self.create_user("target@example.com", self.organization)

        response = self.make_delete_request(self.request_user, target.id)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(UserProfile.objects.filter(id=target.id).exists())

    def test_user_cannot_delete_user_in_another_organization(self):
        target = self.create_user("other@example.com", self.other_organization)

        response = self.make_delete_request(self.request_user, target.id)

        self.assertEqual(response.status_code, 404)
        self.assertTrue(UserProfile.objects.filter(id=target.id).exists())

    def test_deleting_nonexistent_user_returns_404(self):
        response = self.make_delete_request(
            self.request_user,
            "00000000-0000-0000-0000-000000000000",
        )

        self.assertEqual(response.status_code, 404)
