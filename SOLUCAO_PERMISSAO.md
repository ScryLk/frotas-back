# Solução: Erro de Permissão ao Criar Usuário

## ❌ Erro Atual

```json
{
  "status": "error",
  "message": "Você não tem permissão para executar essa ação.",
  "errors": {
    "detail": "Você não tem permissão para executar essa ação."
  }
}
```

## 🔍 Causa

O endpoint `/api/auth/admin/users/` requer permissão de **administrador** (`IsAdminUser`).

Para usar este endpoint, o usuário precisa ter:
- `is_staff = True` **OU**
- `is_superuser = True`

---

## ✅ Solução 1: Tornar o Usuário Atual Admin (Recomendado)

### Opção A: Usar script Python

```bash
# Ative o virtualenv
source venv/bin/activate

# Execute o script (substitua 'seu_username' pelo username real)
python make_admin.py seu_username
```

### Opção B: Via Django Shell

```bash
source venv/bin/activate
python manage.py shell
```

Depois execute:

```python
from django.contrib.auth.models import User

# Substitua 'seu_username' pelo username do usuário logado
username = 'seu_username'

user = User.objects.get(username=username)
user.is_staff = True
user.is_superuser = True
user.save()

print(f"✅ {username} agora é admin!")
```

### Opção C: Via Admin do Django

1. Acesse: `http://localhost:8000/admin/`
2. Faça login com um superusuário
3. Vá em **Users**
4. Selecione o usuário
5. Marque as opções:
   - ✅ Staff status
   - ✅ Superuser status
6. Salve

---

## ✅ Solução 2: Criar Endpoint Sem Permissão de Admin (Não Recomendado)

Se você não quer exigir admin para criar usuários, pode criar um endpoint alternativo.

### Adicione em `authapi/views.py`:

```python
class PublicUserCreateView(APIView):
    """
    Endpoint para criar usuários SEM exigir permissão de admin.
    ⚠️ USE COM CUIDADO! Qualquer usuário autenticado pode criar outros usuários.
    """
    permission_classes = [permissions.IsAuthenticated]  # Apenas autenticado, não admin

    @extend_schema(
        summary='Criar usuário (sem exigir admin)',
        tags=['Auth'],
        request=UserAdminSerializer,
        responses={201: 'authapi.serializers.UserResponseSerializer', 400: ErrorResponseSerializer},
    )
    def post(self, request):
        serializer = UserAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({'status': 'success', 'data': UserPublicSerializer(user).data}, status=status.HTTP_201_CREATED)
```

### Adicione em `authapi/urls.py`:

```python
from .views import PublicUserCreateView  # Adicione ao import

urlpatterns = [
    # ... outras rotas
    path('users/create/', PublicUserCreateView.as_view(), name='public_user_create'),
]
```

Depois use o endpoint: `POST /api/auth/users/create/`

⚠️ **ATENÇÃO:** Esta abordagem permite que qualquer usuário autenticado crie novos usuários, o que pode ser um risco de segurança.

---

## ✅ Solução 3: Criar Superusuário Inicial

Se você ainda não tem nenhum admin, crie um:

```bash
source venv/bin/activate
python manage.py createsuperuser
```

Siga as instruções:
- Username: `admin`
- Email: `admin@example.com`
- Password: (mínimo 10 caracteres)

Depois faça login com este usuário para ter permissões de admin.

---

## 🧪 Verificar Permissões do Usuário Atual

### Via API

**GET** `/api/auth/me/`

```bash
curl -X GET http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer SEU_TOKEN"
```

Resposta:

```json
{
  "status": "success",
  "data": {
    "id": 1,
    "username": "usuario",
    "is_superuser": false  // ⚠️ Precisa ser true para criar usuários
  }
}
```

### Via Django Shell

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User

# Liste todos os usuários e suas permissões
for user in User.objects.all():
    print(f"{user.username}:")
    print(f"  - Staff: {user.is_staff}")
    print(f"  - Superuser: {user.is_superuser}")
    print()
```

---

## 📝 Resumo

1. **Para usar `/api/auth/admin/users/`**: Usuário precisa ser admin
2. **Tornar usuário admin**: Use o script `make_admin.py`
3. **Criar primeiro admin**: Use `python manage.py createsuperuser`
4. **Verificar permissões**: Use `/api/auth/me/` ou Django shell

---

## 🔒 Recomendação de Segurança

Mantenha o endpoint `/api/auth/admin/users/` com a permissão `IsAdminUser`. Isso é uma boa prática de segurança que previne:

- Criação não autorizada de contas
- Escalação de privilégios
- Spam de usuários falsos

Apenas administradores devem ter a capacidade de criar novos usuários no sistema.
