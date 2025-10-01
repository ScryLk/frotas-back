from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.authentication import BaseAuthentication
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework_simplejwt.views import TokenObtainPairView as BaseTokenObtainPairView, TokenRefreshView as BaseTokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import CustomTokenObtainPairSerializer, CustomTokenRefreshSerializer, RegistrationSerializer, UserPublicSerializer, RegisterResponseSerializer, TokenObtainPairResponseSerializer, TokenRefreshResponseSerializer, MeResponseSerializer, LoginRequestSerializer
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
                        'last_name': 'Doe'
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
