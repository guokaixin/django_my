from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from collections import OrderedDict


class CommonPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 10000

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('page_count', self.page.paginator.num_pages),
            ('page_number', self.page.number),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class OnePageNumberPagination(CommonPageNumberPagination):
    page_size = 999
