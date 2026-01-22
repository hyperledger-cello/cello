from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.response import Response

from chaincode.serializers import ChaincodeSerializer

# Create your views here.
class ChaincodeViewSet(viewsets.ViewSet):
    @extend_schema(
        request=ChaincodeSerializer,
        responses={201: ChaincodeSerializer}
    )
    def create(self, request):
        serializer = ChaincodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.validated_data, status=status.HTTP_201_CREATED)
