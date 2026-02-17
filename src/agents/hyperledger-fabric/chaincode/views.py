from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response

from chaincode.serializers import ChaincodeCreationSerializer, ChaincodeInstallationSerializer, \
    ChaincodeApprovementSerializer, ChaincodeCommitSerializer


# Create your views here.
class ChaincodeViewSet(viewsets.ViewSet):
    def get_parsers(self):
        request_action = getattr(self, 'action', None)
        if request_action is not None:
            if request_action == 'create' or request_action == 'install':
                return [MultiPartParser()]
            else:
                return [JSONParser()]
        return [MultiPartParser(), JSONParser()]

    @extend_schema(
        request=ChaincodeCreationSerializer,
        responses={201: None}
    )
    def create(self, request):
        serializer = ChaincodeCreationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)

    @extend_schema(
        request=ChaincodeInstallationSerializer,
        responses={204: None}
    )
    @action(detail=False, methods=["PUT"])
    def install(self, request):
        serializer = ChaincodeInstallationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        request=ChaincodeApprovementSerializer,
        responses={204: None}
    )
    @action(detail=False, methods=["PUT"])
    def approve(self, request):
        serializer = ChaincodeApprovementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        request=ChaincodeCommitSerializer,
        responses={204: None}
    )
    @action(detail=False, methods=["PUT"])
    def commit(self, request):
        serializer = ChaincodeCommitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
