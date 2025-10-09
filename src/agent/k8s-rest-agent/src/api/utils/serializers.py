import textwrap

from rest_framework import serializers
from api.utils.enums import ErrorCode


class PaginationSerializer(serializers.Serializer):
    page = serializers.IntegerField(
        default=1, min_value=1, help_text="查询第几页"
    )
    per_page = serializers.IntegerField(
        default=10,
        min_value=-1,
        help_text="查询分页的每页数量, 如果为-1则不限制分页数量",
    )
    limit = serializers.IntegerField(
        min_value=1, help_text="限制最大数量", required=False
    )


class PaginationResultSerializer(serializers.Serializer):
    total = serializers.IntegerField(
        min_value=0, help_text="Total Number of result"
    )


class BadResponseSerializer(serializers.Serializer):
    code = serializers.IntegerField(
        help_text=textwrap.dedent(ErrorCode.get_info())
    )
    detail = serializers.CharField(
        required=False, help_text="Error Messages", allow_blank=True
    )
