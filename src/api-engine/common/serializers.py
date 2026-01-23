from django.core.paginator import Paginator
from django.db.models import QuerySet
from rest_framework import serializers


class PageQuerySerializer(serializers.Serializer):
    page = serializers.IntegerField(
        help_text="Page of filter", default=1, min_value=1
    )
    per_page = serializers.IntegerField(
        default=10, help_text="Per Page of filter", min_value=1, max_value=100
    )

    def get_paginator(self, q: QuerySet) -> Paginator:
        self.is_valid(raise_exception=True)
        return Paginator(q, self.data['per_page'])


class ListResponseSerializer(serializers.Serializer):
    total = serializers.IntegerField(
        help_text="Total number of data", min_value=0
    )
