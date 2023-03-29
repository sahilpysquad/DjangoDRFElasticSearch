import abc
from abc import ABC

from django.http import HttpResponse
from django.views.generic import TemplateView
from elasticsearch_dsl import Q
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from blog.documents import ArticleDocument, UserDocument, CategoryDocument
from blog.serializers import ArticleSerializer, UserSerializer, CategorySerializer


class PaginatedElasticSearchAPIView(APIView, LimitOffsetPagination):
    serializer_class = None
    document_class = None

    @abc.abstractmethod
    def generate_q_expression(self, query):
        """This method should be overridden
        and return a Q() expression."""

    def get(self, request, query):
        try:
            q = self.generate_q_expression(query)
            search = self.document_class.search().query(q)
            response = search.execute()

            print(f'Found {response.hits.total.value} hit(s) for query: "{query}"')

            results = self.paginate_queryset(response, request, view=self)
            serializer = self.serializer_class(results, many=True)
            return self.get_paginated_response(serializer.data)
        except Exception as e:
            return HttpResponse(e, status=500)


# views


class SearchUsers(PaginatedElasticSearchAPIView):
    serializer_class = UserSerializer
    document_class = UserDocument

    def generate_q_expression(self, query):
        return Q('bool',
                 should=[
                     Q('match', username=query),
                     Q('match', first_name=query),
                     Q('match', last_name=query),
                 ], minimum_should_match=1)


class SearchCategories(PaginatedElasticSearchAPIView):
    serializer_class = CategorySerializer
    document_class = CategoryDocument

    def generate_q_expression(self, query):
        return Q(
            'multi_match', query=query,
            fields=[
                'name',
                'description',
            ], fuzziness='auto')


class SearchArticles(PaginatedElasticSearchAPIView):
    serializer_class = ArticleSerializer
    document_class = ArticleDocument

    def generate_q_expression(self, query):
        return Q(
            'multi_match', query=query,
            fields=[
                'title',
                'author',
                'type',
                'content'
            ], fuzziness='auto')


class TestClass(PaginatedElasticSearchAPIView, ABC):
    """This class is made for only testing purpose"""
    # Testing


class SetCookiesAPI(APIView):

    def post(self, request):
        html = HttpResponse("<h1>Dataflair Django Tutorial</h1>")
        html.set_cookie("Hello")
        data = {
            "name": "Sahil",
            "html": str(html)
        }
        return Response(data, status=status.HTTP_200_OK)


class SetCookiesTemplate(TemplateView):
    def get(self, request, *args, **kwargs):
        html = HttpResponse("<h1>PySquad Django Tutorial</h1><br><a href='http://127.0.0.1:8000/get-cookies-html/'><button>Get Cookies</button></a>")
        html.set_cookie("hello", "How are you ?", max_age=5)
        return html


class GetCookiesTemplate(TemplateView):
    template_name = "hello1.html"

    def get(self, request, *args, **kwargs):
        cookie = request.COOKIES.get("hello")
        html = HttpResponse("<h1>This cookies is gotten from {}</h1>".format(cookie))
        cookies = request.COOKIES
        print(cookies)
        return html
