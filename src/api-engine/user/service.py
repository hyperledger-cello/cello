from organization.models import Organization
from user.models import UserProfile


def create_user(organization: Organization, email: str, password: str, role: UserProfile.Role) -> UserProfile:
    user = UserProfile(
        username=email,
        email=email,
        role=role,
        organization=organization,
    )
    user.set_password(password)
    user.save()
    return user
