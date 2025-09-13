from rest_framework import serializers


class PageQuerySerializer(serializers.Serializer):
    page = serializers.IntegerField(
        help_text="Page of filter", default=1, min_value=1
    )
    per_page = serializers.IntegerField(
        default=10, help_text="Per Page of filter", min_value=1, max_value=100
    )

class ListResponseSerializer(serializers.Serializer):
    total = serializers.IntegerField(
        help_text="Total number of data", min_value=0
    )
