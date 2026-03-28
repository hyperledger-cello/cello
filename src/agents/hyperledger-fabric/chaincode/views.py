from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response

from chaincode.serializers import ChaincodeCreationSerializer, ChaincodeInstallationSerializer, \
    ChaincodeApprovementSerializer, ChaincodeCommitSerializer, ChaincodeResponseSerializer, ChaincodeStatusResponse, \
    ChaincodeStatusRequest, ChaincodeCommitReadinessRequest, ChaincodeCommitReadinessResponse


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
        responses={201: ChaincodeResponseSerializer}
    )
    def create(self, request):
        serializer = ChaincodeCreationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            data=serializer.save().data,
            status=status.HTTP_201_CREATED)

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

    @extend_schema(
        parameters=[ChaincodeStatusRequest],
        responses={200: ChaincodeStatusResponse}
    )
    @action(detail=False, methods=["GET"])
    def status(self, request):
        serializer = ChaincodeStatusRequest(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        return Response(
            data=serializer.save().data,
            status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[ChaincodeCommitReadinessRequest],
        responses={200: ChaincodeCommitReadinessResponse}
    )
    @action(detail=False, methods=["GET"], url_path="commit/readiness")
    def commit_readiness(self, request):
        serializer = ChaincodeCommitReadinessRequest(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        return Response(
            data=serializer.save().data,
            status=status.HTTP_200_OK)
