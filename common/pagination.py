"""Pagination styles used across the resource APIs."""

from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.response import Response


class ListPagination(PageNumberPagination):
    """Default page/limit pagination for resource collections."""

    page_size = 50
    page_size_query_param = 'limit'
    max_page_size = 500

    def get_paginated_response(self, data):
        return Response({
            'items': data,
            'total': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
        })


class EventPagination(CursorPagination):
    """Stable ordering for append-only streams (events, agent reports)."""

    page_size = 100
    max_page_size = 1000
    page_size_query_param = 'limit'
    ordering = '-created_at'
