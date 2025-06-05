from rest_framework.pagination import PageNumberPagination

from .constants import PAGE_SIZE_DEFAULT


class LimitPageNumberPagination(PageNumberPagination):
    page_size = PAGE_SIZE_DEFAULT
    page_size_query_param = "limit"
