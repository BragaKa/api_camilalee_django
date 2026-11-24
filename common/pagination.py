from rest_framework.pagination import PageNumberPagination


class PaginacaoPadrao(PageNumberPagination):
    """Paginação por página: ?page=2&page_size=20 (máximo de 100 por página)."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
