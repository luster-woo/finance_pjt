from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """
    기본 페이지네이션.

    ?page=2           → 2페이지
    ?page_size=50     → 페이지당 50개 (최대 100)
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
