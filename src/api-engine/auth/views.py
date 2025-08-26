from rest_framework import viewsets

from api.models import Organization
from auth.serializers import RegisterBody


class RegisterViewSet(viewsets.ViewSet):
    def create(self, request):
        try:
            serializer = RegisterBody(data=request.data)
            serializer.is_valid(raise_exception=True)
            email = serializer.validated_data.get("email")
            org_name = serializer.validated_data.get("orgName")
            password = serializer.validated_data.get("password")

            try:
                UserProfile.objects.get(email=email)
            except ObjectDoesNotExist:
                pass
            except MultipleObjectsReturned:
                return Response(
                    err("Email Aleady exists!"),
                    status=status.HTTP_409_CONFLICT,
                )
            else:
                return Response(
                    err("Email Aleady exists!"),
                    status=status.HTTP_409_CONFLICT,
                )

            try:
                Organization.objects.get(name=org_name)
            except ObjectDoesNotExist:
                pass
            except MultipleObjectsReturned:
                return Response(
                    err("Orgnization already exists!"),
                    status=status.HTTP_409_CONFLICT,
                )
            else:
                return Response(
                    err("Orgnization already exists!"),
                    status=status.HTTP_409_CONFLICT,
                )

            CryptoConfig(org_name).create(0, 0)
            CryptoGen(org_name).generate()

            organization = Organization(name=org_name)
            organization.save()

            user = UserProfile(
                email=email,
                role="admin",
                organization=organization,
            )
            user.set_password(password)
            user.save()

            response = RegisterResponse(data={"id": organization.id})
            if response.is_valid(raise_exception=True):
                return Response(
                    data=ok(response.validated_data),
                    status=status.HTTP_200_OK,
                )
        except Exception as e:
            return Response(err(e.args), status=status.HTTP_400_BAD_REQUEST)