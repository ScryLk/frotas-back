from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .models import Secretaria, Carro, Viagem, Motorista, Localizacao
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
    MotoristaSerializer,
    MotoristaListResponseSerializer,
    LocalizacaoSerializer,
    LocalizacaoResponseSerializer,
    LocalizacaoListResponseSerializer,
)
from core.serializers import ErrorResponseSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly


class IsSuperUserOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class IsStaffOrSuperUserOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        u = request.user
        return bool(u and u.is_authenticated and (u.is_staff or u.is_superuser))


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
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
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
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # Filtros básicos para apoiar relatórios e listagens
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = {
        'secretaria': ['exact'],
        'carro': ['exact'],
        'motorista': ['exact'],
        'status': ['exact', 'in'],
        'data_saida': ['gte', 'lte', 'date__gte', 'date__lte'],
    }
    ordering_fields = ['data_saida', 'criado_em']

    def _period_filter(self, qs, request):
        # Parâmetros de período agora são opcionais. Quando ausentes/blank, considera "todo o período" (sem filtro por data).
        def _norm(v):
            if v is None:
                return None
            v2 = str(v).strip().lower()
            return None if v2 in ('', 'null', 'none', 'undefined') else v

        def _parse_dt(v):
            try:
                return datetime.fromisoformat(v)
            except Exception:
                d = parse_date(v)
                if d:
                    return datetime.combine(d, datetime.min.time())
            return None

        data_ini = _norm(request.query_params.get('data_ini'))
        data_fim = _norm(request.query_params.get('data_fim'))

        if data_ini:
            dt_ini = _parse_dt(data_ini)
            if dt_ini:
                qs = qs.filter(data_saida__gte=dt_ini)
        if data_fim:
            # usar fim do dia quando data sem hora
            dt_fim = None
            try:
                dt_fim = datetime.fromisoformat(data_fim)
            except Exception:
                d = parse_date(data_fim)
                if d:
                    dt_fim = datetime.combine(d, datetime.max.time())
            if dt_fim:
                qs = qs.filter(data_saida__lte=dt_fim)

        status_param = request.query_params.get('status')
        if status_param:
            statuses = [s.strip() for s in str(status_param).split(',') if s and s.strip()]
            if statuses:
                qs = qs.filter(status__in(statuses))
        return qs

    @extend_schema(responses={200: ViagemListResponseSerializer, 401: ErrorResponseSerializer})
    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        qs = self._period_filter(qs, request)
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

    @extend_schema(summary='Totais de viagens', description='Se data_ini/data_fim não forem informados, considera todo o período (dados de todo o sistema).', tags=['Relatórios'], responses={200: 'frotas.serializers.ViagensTotaisResponseSerializer'})
    @action(detail=False, methods=['get'], url_path='totais', permission_classes=[permissions.IsAuthenticated])
    def totais(self, request):
        qs = self._period_filter(self.get_queryset(), request)
        total = qs.count()
        by_status_rows = qs.values('status').annotate(c=Count('id'))
        by_status = {row['status']: row['c'] for row in by_status_rows}
        data = {
            'total': total,
            'em_andamento': by_status.get(Viagem.Status.EM_ANDAMENTO, 0),
            'concluida': by_status.get(Viagem.Status.CONCLUIDA, 0),
            'cancelada': by_status.get(Viagem.Status.CANCELADA, 0),
        }
        return Response({'status': 'success', 'data': data})

    @extend_schema(summary='Série temporal de viagens por dia', description='Se data_ini/data_fim não forem informados, considera todo o período (dados de todo o sistema).', tags=['Relatórios'], responses={200: 'frotas.serializers.ViagensSerieResponseSerializer'})
    @action(detail=False, methods=['get'], url_path='serie', permission_classes=[permissions.IsAuthenticated])
    def serie(self, request):
        qs = self._period_filter(self.get_queryset(), request)
        serie = (
            qs.annotate(periodo=TruncDate('data_saida'))
              .values('periodo')
              .annotate(total=Count('id'))
              .order_by('periodo')
        )
        data = [{'periodo': i['periodo'].isoformat(), 'total': i['total']} for i in serie]
        return Response({'status': 'success', 'data': data})

    @extend_schema(summary='KM por secretaria (aprox. por diferença de odômetros)', description='Se data_ini/data_fim não forem informados, considera todo o período (dados de todo o sistema).', tags=['Relatórios'], responses={200: 'frotas.serializers.ViagensKmPorSecretariaResponseSerializer'})
    @action(detail=False, methods=['get'], url_path='km_por_secretaria', permission_classes=[permissions.IsAuthenticated])
    def km_por_secretaria(self, request):
        qs = self._period_filter(self.get_queryset(), request)
        # Somatório simples de (odometro_chegada - odometro_saida) quando ambos informados
        rows = (
            qs.exclude(odometro_chegada__isnull=True)
              .values('secretaria__id', 'secretaria__nome')
              .annotate(total_km=Count('id'))  # placeholder para estrutura
        )
        # Recalcular manualmente total_km pois agregação por diferença não é suportada em Count
        totals = {}
        for v in qs.exclude(odometro_chegada__isnull=True).select_related('secretaria'):
            delta = max(0, (v.odometro_chegada or 0) - (v.odometro_saida or 0))
            sid = v.secretaria.id
            totals.setdefault(sid, {'secretaria': sid, 'nome': v.secretaria.nome, 'total_km': 0})
            totals[sid]['total_km'] += delta
        data = list(totals.values())
        data.sort(key=lambda x: x['nome'])
        return Response({'status': 'success', 'data': data})

    @extend_schema(summary='Top destinos', description='Se data_ini/data_fim não forem informados, considera todo o período (dados de todo o sistema). Parâmetro limit é opcional.', tags=['Relatórios'], responses={200: 'frotas.serializers.ViagensTopDestinosResponseSerializer'})
    @action(detail=False, methods=['get'], url_path='top_destinos', permission_classes=[permissions.IsAuthenticated])
    def top_destinos(self, request):
        qs = self._period_filter(self.get_queryset(), request)
        limit_raw = request.query_params.get('limit')
        try:
            limit = int(limit_raw) if limit_raw not in (None, '', 'null', 'None') else 10
        except Exception:
            limit = 10
        limit = max(1, min(limit, 100))
        # Preferir nome da Localizacao quando houver, senão usar destino textual
        agg = (
            qs.values('localizacao__nome', 'destino')
              .annotate(total=Count('id'))
              .order_by('-total')
        )
        items = []
        for row in agg:
            nome = row['localizacao__nome'] or row['destino']
            if not nome:
                continue
            items.append({'destino': nome, 'total': row['total']})
            if len(items) >= limit:
                break
        return Response({'status': 'success', 'data': items})


@extend_schema(tags=['Motoristas'])
class MotoristaViewSet(viewsets.ModelViewSet):
    queryset = Motorista.objects.all().order_by('nome')
    serializer_class = MotoristaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = {
        'nome': ['icontains', 'exact'],
    }
    ordering_fields = ['nome', 'criado_em']
    search_fields = ['nome']

    class _Paginator(PageNumberPagination):
        page_size = 10
        page_size_query_param = 'page_size'

    pagination_class = _Paginator

    @extend_schema(responses={200: MotoristaListResponseSerializer, 401: ErrorResponseSerializer})
    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            page_payload = self.paginator.get_paginated_response(serializer.data).data
            return Response({'status': 'success', 'data': page_payload})
        serializer = self.get_serializer(qs, many=True)
        return Response({'status': 'success', 'data': {'count': len(serializer.data), 'next': None, 'previous': None, 'results': serializer.data}})

    @extend_schema(responses={201: 'frotas.serializers.MotoristaResponseSerializer', 401: ErrorResponseSerializer, 403: ErrorResponseSerializer, 400: ErrorResponseSerializer})
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_201_CREATED)

    @extend_schema(responses={200: 'frotas.serializers.MotoristaResponseSerializer', 401: ErrorResponseSerializer, 404: ErrorResponseSerializer})
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'status': 'success', 'data': serializer.data})

    @extend_schema(responses={200: 'frotas.serializers.MotoristaResponseSerializer', 401: ErrorResponseSerializer, 403: ErrorResponseSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer})
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


@extend_schema(tags=['Localizações'])
class LocalizacaoViewSet(viewsets.ModelViewSet):
    queryset = Localizacao.objects.all().order_by('nome')
    serializer_class = LocalizacaoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @extend_schema(responses={200: LocalizacaoListResponseSerializer, 401: 'core.serializers.ErrorResponseSerializer'})
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response({'status': 'success', 'data': serializer.data})

    @extend_schema(responses={201: LocalizacaoResponseSerializer, 401: 'core.serializers.ErrorResponseSerializer', 403: 'core.serializers.ErrorResponseSerializer', 400: 'core.serializers.ErrorResponseSerializer'})
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_201_CREATED)

    @extend_schema(responses={200: LocalizacaoResponseSerializer, 401: 'core.serializers.ErrorResponseSerializer', 404: 'core.serializers.ErrorResponseSerializer'})
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'status': 'success', 'data': serializer.data})

    @extend_schema(responses={200: LocalizacaoResponseSerializer, 401: 'core.serializers.ErrorResponseSerializer', 403: 'core.serializers.ErrorResponseSerializer', 400: 'core.serializers.ErrorResponseSerializer', 404: 'core.serializers.ErrorResponseSerializer'})
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'status': 'success', 'data': serializer.data})

    @extend_schema(responses={200: None, 401: 'core.serializers.ErrorResponseSerializer', 403: 'core.serializers.ErrorResponseSerializer', 404: 'core.serializers.ErrorResponseSerializer'})
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'status': 'success', 'data': None}, status=status.HTTP_200_OK)


@extend_schema(tags=['Relatórios'])
class RelatoriosViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def _qs(self, request):
        view = ViagemViewSet()
        view.request = request
        view.kwargs = {}
        return view._period_filter(Viagem.objects.all(), request)

    @extend_schema(summary='Totais de viagens', description='Se data_ini/data_fim não forem informados, considera todo o período (dados de todo o sistema).', responses={200: 'frotas.serializers.ViagensTotaisResponseSerializer'})
    def list(self, request):
        qs = self._qs(request)
        total = qs.count()
        by_status_rows = qs.values('status').annotate(c=Count('id'))
        by_status = {row['status']: row['c'] for row in by_status_rows}
        data = {
            'total': total,
            'em_andamento': by_status.get(Viagem.Status.EM_ANDAMENTO, 0),
            'concluida': by_status.get(Viagem.Status.CONCLUIDA, 0),
            'cancelada': by_status.get(Viagem.Status.CANCELADA, 0),
        }
        return Response({'status': 'success', 'data': data})

    @extend_schema(summary='Totais de viagens', description='Se data_ini/data_fim não forem informados, considera todo o período (dados de todo o sistema).', responses={200: 'frotas.serializers.ViagensTotaisResponseSerializer'})
    @action(detail=False, methods=['get'], url_path='totais')
    def totais(self, request):
        qs = self._qs(request)
        total = qs.count()
        by_status_rows = qs.values('status').annotate(c=Count('id'))
        by_status = {row['status']: row['c'] for row in by_status_rows}
        data = {
            'total': total,
            'em_andamento': by_status.get(Viagem.Status.EM_ANDAMENTO, 0),
            'concluida': by_status.get(Viagem.Status.CONCLUIDA, 0),
            'cancelada': by_status.get(Viagem.Status.CANCELADA, 0),
        }
        return Response({'status': 'success', 'data': data})

    @extend_schema(summary='Série temporal de viagens por dia', description='Se data_ini/data_fim não forem informados, considera todo o período (dados de todo o sistema).', responses={200: 'frotas.serializers.ViagensSerieResponseSerializer'})
    @action(detail=False, methods=['get'], url_path='serie')
    def serie(self, request):
        view = ViagemViewSet()
        view.request = request
        view.kwargs = {}
        return view.serie(request)

    @extend_schema(summary='KM por secretaria', description='Se data_ini/data_fim não forem informados, considera todo o período (dados de todo o sistema).', responses={200: 'frotas.serializers.ViagensKmPorSecretariaResponseSerializer'})
    @action(detail=False, methods=['get'], url_path='km_por_secretaria')
    def km_por_secretaria(self, request):
        view = ViagemViewSet()
        view.request = request
        view.kwargs = {}
        return view.km_por_secretaria(request)

    @extend_schema(summary='Top destinos', description='Se data_ini/data_fim não forem informados, considera todo o período (dados de todo o sistema). Parâmetro limit é opcional.', responses={200: 'frotas.serializers.ViagensTopDestinosResponseSerializer'})
    @action(detail=False, methods=['get'], url_path='top_destinos')
    def top_destinos(self, request):
        view = ViagemViewSet()
        view.request = request
        view.kwargs = {}
        return view.top_destinos(request)
