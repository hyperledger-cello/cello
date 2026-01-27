from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class TotalDataPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "per_page"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "total": self.page.paginator.count,
            "data": data
        })
