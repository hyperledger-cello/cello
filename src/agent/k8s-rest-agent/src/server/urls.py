"""server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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

import os

from api.routes.hello.views import HelloViewSet
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.routers import DefaultRouter

DEBUG = getattr(settings, "DEBUG", False)
VERSION = os.getenv("API_VERSION", "v1")

router = DefaultRouter(trailing_slash=False)
router.register("hello", HelloViewSet, basename="hello")

router.include_root_view = False

urlpatterns = router.urls

swagger_info = openapi.Info(
    title="Django Example API",
    default_version=VERSION,
    description="""
        Django Example API 
    """,
)

SchemaView = get_schema_view(
    info=swagger_info,
    validators=["flex"],
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns += [
    path("admin/", admin.site.urls),
    path("jet/", include("jet.urls", "jet")),
]

if DEBUG:
    urlpatterns += [
        path(
            "docs/",
            SchemaView.with_ui("swagger", cache_timeout=0),
            name="docs",
        ),
        path(
            "redoc/",
            SchemaView.with_ui("redoc", cache_timeout=0),
            name="redoc",
        ),
    ]
