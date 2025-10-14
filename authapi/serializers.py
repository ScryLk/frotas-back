from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from django.contrib.auth.password_validation import validate_password
from django.conf import settings


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.get_username()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        # Verifica se o usuário precisa trocar a senha
        require_password_change = getattr(user.profile, 'require_password_change', False) if hasattr(user, 'profile') else False
        return {
            'status': 'success',
            'data': {
                'access': data['access'],
                'refresh': data['refresh'],
                'require_password_change': require_password_change,
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


class UserListResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = UserPublicSerializer(many=True)


class UserAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False, min_length=getattr(settings, 'PASSWORD_MIN_LENGTH', 8))

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'is_staff', 'is_superuser', 'password'
        )
        read_only_fields = ('id',)

    def validate_username(self, value):
        qs = User.objects.filter(username=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Username já em uso.')
        return value

    def validate_email(self, value):
        if not value:
            return value
        qs = User.objects.filter(email=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Email já em uso.')
        return value

    def validate(self, attrs):
        pwd = attrs.get('password')
        if pwd:
            user_for_validation = self.instance or User(
                username=attrs.get('username') or getattr(self.instance, 'username', ''),
                email=attrs.get('email') or getattr(self.instance, 'email', ''),
                first_name=attrs.get('first_name') or getattr(self.instance, 'first_name', ''),
                last_name=attrs.get('last_name') or getattr(self.instance, 'last_name', ''),
            )
            validate_password(pwd, user=user_for_validation)
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save(update_fields=['password'])
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=getattr(settings, 'PASSWORD_MIN_LENGTH', 8))

    def validate(self, attrs):
        user = self.context['user']
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError({'old_password': 'Senha atual incorreta.'})
        validate_password(attrs['new_password'], user=user)
        return attrs


class PasswordSetSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, min_length=getattr(settings, 'PASSWORD_MIN_LENGTH', 8))

    def validate_new_password(self, value):
        validate_password(value, user=self.context['user'])
        return value


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=getattr(settings, 'PASSWORD_MIN_LENGTH', 8))
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
    data = serializers.DictField(child=serializers.CharField())
    # Para documentação, detalhar os campos esperados
    # id, username, email, first_name, last_name, is_superuser


class UserResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = UserPublicSerializer()


class FirstAccessPasswordChangeSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, min_length=getattr(settings, 'PASSWORD_MIN_LENGTH', 8))
    confirm_password = serializers.CharField(write_only=True, min_length=getattr(settings, 'PASSWORD_MIN_LENGTH', 8))

    def validate(self, attrs):
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

        if new_password != confirm_password:
            raise serializers.ValidationError({'confirm_password': 'As senhas não conferem.'})

        # Valida a nova senha
        user = self.context.get('user')
        if user:
            validate_password(new_password, user=user)

        return attrs
