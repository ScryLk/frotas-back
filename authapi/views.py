from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.authentication import BaseAuthentication
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework_simplejwt.views import TokenObtainPairView as BaseTokenObtainPairView, TokenRefreshView as BaseTokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import CustomTokenObtainPairSerializer, CustomTokenRefreshSerializer, RegistrationSerializer, UserPublicSerializer, RegisterResponseSerializer, TokenObtainPairResponseSerializer, TokenRefreshResponseSerializer, MeResponseSerializer, LoginRequestSerializer, UserListResponseSerializer, UserAdminSerializer, PasswordChangeSerializer, PasswordSetSerializer
from django.contrib.auth.models import User
from rest_framework import status
from core.serializers import ErrorResponseSerializer


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Dados do usuário autenticado',
        tags=['Auth'],
        responses={200: MeResponseSerializer, 401: ErrorResponseSerializer},
        examples=[
            OpenApiExample(
                'Sucesso',
                value={
                    'status': 'success',
                    'data': {
                        'id': 'uuid',
                        'username': 'jdoe',
                        'email': 'jdoe@example.com',
                        'first_name': 'John',
                        'last_name': 'Doe',
                        'is_superuser': True
                    }
                },
            )
        ],
    )
    def get(self, request):
        user = request.user
        return Response({
            'status': 'success',
            'data': {
                'id': user.id,
                'username': user.username,
                'email': getattr(user, 'email', ''),
                'first_name': getattr(user, 'first_name', ''),
                'last_name': getattr(user, 'last_name', ''),
                'is_superuser': getattr(user, 'is_superuser', False),
            }
        })


class TokenObtainPairView(BaseTokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer

    @extend_schema(
        summary='Obter tokens JWT',
        tags=['Auth'],
        request=CustomTokenObtainPairSerializer,
        responses={200: TokenObtainPairResponseSerializer, 401: ErrorResponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TokenRefreshView(BaseTokenRefreshView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenRefreshSerializer

    @extend_schema(
        summary='Renovar token de acesso',
        tags=['Auth'],
        request=CustomTokenRefreshSerializer,
        responses={200: TokenRefreshResponseSerializer, 401: ErrorResponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # ignora Authorization header

    @extend_schema(
        summary='Cadastro de usuário',
        tags=['Auth'],
        auth=[],  # remove bearer do endpoint no Swagger
        request=RegistrationSerializer,
        responses={201: RegisterResponseSerializer, 400: ErrorResponseSerializer},
    )
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({'status': 'success', 'data': UserPublicSerializer(user).data}, status=status.HTTP_201_CREATED)
        return Response({'status': 'error', 'message': 'Dados inválidos', 'errors': serializer.errors}, status=400)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        summary='Login (usuário e senha)',
        tags=['Auth'],
        auth=[],
        request=LoginRequestSerializer,
        responses={200: TokenObtainPairResponseSerializer, 400: ErrorResponseSerializer, 401: ErrorResponseSerializer},
    )
    def post(self, request):
        serializer = LoginRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'status': 'error', 'message': 'Dados inválidos', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({'status': 'error', 'message': 'Credenciais inválidas', 'errors': {'non_field_errors': ['Credenciais inválidas']}}, status=401)
        refresh = RefreshToken.for_user(user)
        return Response({
            'status': 'success',
            'data': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.get_username(),
                    'email': getattr(user, 'email', ''),
                    'first_name': getattr(user, 'first_name', ''),
                    'last_name': getattr(user, 'last_name', ''),
                }
            }
        })


class UsersListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Listar usuários de autenticação (auth_user)',
        tags=['Auth'],
        responses={200: UserListResponseSerializer, 401: ErrorResponseSerializer},
    )
    def get(self, request):
        users = User.objects.all().order_by('username')
        data = UserPublicSerializer(users, many=True).data
        return Response({'status': 'success', 'data': data})


class UsersAdminViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('username')
    serializer_class = UserAdminSerializer
    permission_classes = [permissions.IsAdminUser]

    @extend_schema(responses={200: UserListResponseSerializer, 401: ErrorResponseSerializer, 403: ErrorResponseSerializer})
    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        serializer = UserPublicSerializer(qs, many=True)
        return Response({'status': 'success', 'data': serializer.data})

    @extend_schema(responses={201: 'authapi.serializers.UserResponseSerializer', 401: ErrorResponseSerializer, 403: ErrorResponseSerializer, 400: ErrorResponseSerializer})
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({'status': 'success', 'data': UserPublicSerializer(user).data}, status=status.HTTP_201_CREATED)

    @extend_schema(responses={200: 'authapi.serializers.UserResponseSerializer', 401: ErrorResponseSerializer, 403: ErrorResponseSerializer, 404: ErrorResponseSerializer})
    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        return Response({'status': 'success', 'data': UserPublicSerializer(user).data})

    @extend_schema(responses={200: 'authapi.serializers.UserResponseSerializer', 401: ErrorResponseSerializer, 403: ErrorResponseSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer})
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({'status': 'success', 'data': UserPublicSerializer(user).data})

    @extend_schema(responses={200: None, 401: ErrorResponseSerializer, 403: ErrorResponseSerializer, 404: ErrorResponseSerializer})
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({'status': 'success', 'data': None}, status=status.HTTP_200_OK)

    @extend_schema(summary='Alterar própria senha', request=PasswordChangeSerializer, responses={200: None, 401: ErrorResponseSerializer, 400: ErrorResponseSerializer}, tags=['Auth'])
    @action(detail=False, methods=['post'], url_path='password/change', permission_classes=[permissions.IsAuthenticated])
    def password_change(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password'])
        return Response({'status': 'success', 'data': None})

    @extend_schema(summary='Definir senha de um usuário (admin)', request=PasswordSetSerializer, responses={200: None, 401: ErrorResponseSerializer, 403: ErrorResponseSerializer, 404: ErrorResponseSerializer, 400: ErrorResponseSerializer}, tags=['Auth'])
    @action(detail=True, methods=['post'], url_path='password/set', permission_classes=[permissions.IsAdminUser])
    def password_set(self, request, pk=None):
        user = self.get_object()
        serializer = PasswordSetSerializer(data=request.data, context={'user': user})
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        return Response({'status': 'success', 'data': None})
