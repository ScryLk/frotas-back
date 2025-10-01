from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from django.contrib.auth.password_validation import validate_password


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.get_username()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        return {
            'status': 'success',
            'data': {
                'access': data['access'],
                'refresh': data['refresh'],
                'user': {
                    'id': user.id,
                    'username': user.get_username(),
                    'email': getattr(user, 'email', ''),
                    'first_name': getattr(user, 'first_name', ''),
                    'last_name': getattr(user, 'last_name', ''),
                }
            }
        }


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        return {
            'status': 'success',
            'data': data,
        }


class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = fields


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=10)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name')

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username já em uso.')
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email já em uso.')
        return value

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError({'password2': 'As senhas não conferem.'})
        # Monta um usuário temporário para validações de similaridade
        temp_user = User(
            username=attrs.get('username'),
            email=attrs.get('email'),
            first_name=attrs.get('first_name') or '',
            last_name=attrs.get('last_name') or '',
        )
        validate_password(attrs['password'], user=temp_user)
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2', None)
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


# Serializers apenas para documentação das respostas envelope
class RegisterResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = UserPublicSerializer()


class TokenPairDataSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserPublicSerializer()


class TokenObtainPairResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = TokenPairDataSerializer()


class TokenRefreshDataSerializer(serializers.Serializer):
    access = serializers.CharField()


class TokenRefreshResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = TokenRefreshDataSerializer()


class MeResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = UserPublicSerializer()
