#
# SPDX-License-Identifier: Apache-2.0
#
"""api_engine URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.urls import path, include
from rest_framework import permissions
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from django.conf.urls.static import static
from api_engine.settings import DEBUG, WEBROOT
from auth.views import RegisterViewSet, CelloTokenObtainPairView, CelloTokenVerifyView
from chaincode.views import ChaincodeViewSet
from channel.views import ChannelViewSet
from node.views import NodeViewSet
from organization.views import OrganizationViewSet
from user.views import UserViewSet

swagger_info = openapi.Info(
    title="Cello API Engine Service",
    default_version="1.0",
    description="""
    This is swagger docs for Cello API engine.
    """,
)

schema_view = get_schema_view(
    validators=["ssv", "flex"],
    public=True,
    permission_classes=[permissions.AllowAny],
)

# define and register routers of api
router = DefaultRouter(trailing_slash=False)
router.register("organizations", OrganizationViewSet, basename="organization")
router.register("users", UserViewSet, basename="user")
router.register("node", NodeViewSet, basename="node")
router.register("register", RegisterViewSet, basename="register")
router.register("channels", ChannelViewSet, basename="channel")
router.register("chaincodes", ChaincodeViewSet, basename="chaincode")

urlpatterns = [path(WEBROOT, include(router.urls + [
    path(
        "login", CelloTokenObtainPairView.as_view(), name="token_obtain_pair"
    ),
    path("login/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path("token-verify", CelloTokenVerifyView.as_view(), name="token_verify"),
    path("docs", schema_view.with_ui("swagger", cache_timeout=0), name="docs"),
    path("redoc", schema_view.with_ui("redoc", cache_timeout=0), name="redoc"),
]))]

if DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    ) + static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
