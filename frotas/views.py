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
)
from core.serializers import ErrorResponseSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter


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
    }
    ordering_fields = ['placa', 'modelo', 'ano', 'criado_em']
    search_fields = ['placa', 'modelo']

    @extend_schema(responses={200: CarroListResponseSerializer, 401: ErrorResponseSerializer})
    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(qs, many=True)
        return Response({'status': 'success', 'data': serializer.data})

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
