from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .models import Secretaria, Carro, Viagem
from .serializers import (
    SecretariaSerializer,
    CarroSerializer,
    SecretariaResponseSerializer,
    SecretariaListResponseSerializer,
    CarroResponseSerializer,
    CarroListResponseSerializer,
    ViagemSerializer,
    ViagemResponseSerializer,
    ViagemListResponseSerializer,
    SecretariaViagensCountResponseSerializer,
)
from core.serializers import ErrorResponseSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from django.db.models import Count


class IsSuperUserOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


@extend_schema(tags=['Secretarias'])
class SecretariaViewSet(viewsets.ModelViewSet):
    queryset = Secretaria.objects.all().order_by('nome')
    serializer_class = SecretariaSerializer
    permission_classes = [IsSuperUserOrReadOnly]

    @extend_schema(responses={200: SecretariaListResponseSerializer, 401: ErrorResponseSerializer})
    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(qs, many=True)
        return Response({'status': 'success', 'data': serializer.data})

    @extend_schema(responses={201: SecretariaResponseSerializer, 401: ErrorResponseSerializer, 403: ErrorResponseSerializer, 400: ErrorResponseSerializer})
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_201_CREATED)

    @extend_schema(responses={200: SecretariaResponseSerializer, 401: ErrorResponseSerializer, 404: ErrorResponseSerializer})
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'status': 'success', 'data': serializer.data})

    @extend_schema(responses={200: SecretariaResponseSerializer, 401: ErrorResponseSerializer, 403: ErrorResponseSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer})
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'status': 'success', 'data': serializer.data})

    @extend_schema(responses={200: None, 401: ErrorResponseSerializer, 403: ErrorResponseSerializer, 404: ErrorResponseSerializer})
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'status': 'success', 'data': None}, status=status.HTTP_200_OK)

    @extend_schema(summary='Contagem de viagens por secretaria', responses={200: SecretariaViagensCountResponseSerializer, 401: ErrorResponseSerializer}, tags=['Secretarias'])
    @action(detail=False, methods=['get'], url_path='viagens/count', permission_classes=[permissions.IsAuthenticated])
    def viagens_count(self, request):
        qs = Secretaria.objects.annotate(total_viagens=Count('viagens')).values('id', 'nome', 'total_viagens').order_by('nome')
        return Response({'status': 'success', 'data': list(qs)})

    @extend_schema(summary='Contagem de carros por secretaria', responses={200: 'frotas.serializers.SecretariaCarrosCountResponseSerializer', 401: ErrorResponseSerializer}, tags=['Secretarias'])
    @action(detail=False, methods=['get'], url_path='carros/count', permission_classes=[permissions.IsAuthenticated])
    def carros_count(self, request):
        qs = Secretaria.objects.annotate(total_carros=Count('carros')).values('id', 'nome', 'total_carros').order_by('nome')
        return Response({'status': 'success', 'data': list(qs)})


@extend_schema(tags=['Carros'])
class CarroViewSet(viewsets.ModelViewSet):
    queryset = Carro.objects.select_related('secretaria').all().order_by('placa')
    serializer_class = CarroSerializer
    permission_classes = [IsSuperUserOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = {
        'ativo': ['exact'],
        'secretaria': ['exact'],
        'placa': ['exact', 'icontains'],
        'modelo': ['icontains'],
        'ano': ['exact', 'gte', 'lte', 'in'],
        'odometro_atual': ['exact', 'gte', 'lte', 'isnull'],
    }
    ordering_fields = ['placa', 'modelo', 'ano', 'criado_em', 'odometro_atual']
    search_fields = ['placa', 'modelo']

    class _Paginator(PageNumberPagination):
        page_size = 10
        page_size_query_param = 'page_size'

    pagination_class = _Paginator

    @extend_schema(responses={200: CarroListResponseSerializer, 401: ErrorResponseSerializer})
    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            page_payload = self.paginator.get_paginated_response(serializer.data).data
            return Response({'status': 'success', 'data': page_payload})
        serializer = self.get_serializer(qs, many=True)
        return Response({'status': 'success', 'data': {'count': len(serializer.data), 'next': None, 'previous': None, 'results': serializer.data}})

    @extend_schema(responses={201: CarroResponseSerializer, 401: ErrorResponseSerializer, 403: ErrorResponseSerializer, 400: ErrorResponseSerializer})
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_201_CREATED)

    @extend_schema(responses={200: CarroResponseSerializer, 401: ErrorResponseSerializer, 404: ErrorResponseSerializer})
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'status': 'success', 'data': serializer.data})

    @extend_schema(responses={200: CarroResponseSerializer, 401: ErrorResponseSerializer, 403: ErrorResponseSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer})
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'status': 'success', 'data': serializer.data})

    @extend_schema(responses={200: None, 401: ErrorResponseSerializer, 403: ErrorResponseSerializer, 404: ErrorResponseSerializer})
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'status': 'success', 'data': None}, status=status.HTTP_200_OK)


@extend_schema(tags=['Viagens'])
class ViagemViewSet(viewsets.ModelViewSet):
    queryset = Viagem.objects.select_related('secretaria', 'carro', 'motorista').all().order_by('-data_saida')
    serializer_class = ViagemSerializer
    permission_classes = [IsSuperUserOrReadOnly]

    @extend_schema(responses={200: ViagemListResponseSerializer, 401: ErrorResponseSerializer})
    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(qs, many=True)
        return Response({'status': 'success', 'data': serializer.data})

    @extend_schema(responses={201: ViagemResponseSerializer, 401: ErrorResponseSerializer, 403: ErrorResponseSerializer, 400: ErrorResponseSerializer})
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_201_CREATED)

    @extend_schema(responses={200: ViagemResponseSerializer, 401: ErrorResponseSerializer, 404: ErrorResponseSerializer})
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'status': 'success', 'data': serializer.data})

    @extend_schema(responses={200: ViagemResponseSerializer, 401: ErrorResponseSerializer, 403: ErrorResponseSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer})
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'status': 'success', 'data': serializer.data})

    @extend_schema(responses={200: None, 401: ErrorResponseSerializer, 403: ErrorResponseSerializer, 404: ErrorResponseSerializer})
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'status': 'success', 'data': None}, status=status.HTTP_200_OK)
