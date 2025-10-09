# Guia de Consumo da API - Frontend

## 🔐 Autenticação e Redefinição de Senha no Primeiro Acesso

### Base URL
```
http://localhost:8000
```

---

## 📡 Endpoints Disponíveis

### 1. Login
**POST** `/api/auth/login/`

**Headers:**
```
Content-Type: application/json
```

**Request:**
```json
{
  "username": "usuario",
  "password": "senha123"
}
```

**Response (Sucesso - 200):**
```json
{
  "status": "success",
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "require_password_change": true,
    "user": {
      "id": 1,
      "username": "usuario",
      "email": "user@example.com",
      "first_name": "Nome",
      "last_name": "Sobrenome"
    }
  }
}
```

**Response (Erro - 401):**
```json
{
  "status": "error",
  "message": "Credenciais inválidas",
  "errors": {
    "non_field_errors": ["Credenciais inválidas"]
  }
}
```

**Response (Erro de validação - 400):**
```json
{
  "status": "error",
  "message": "Dados inválidos",
  "errors": {
    "username": ["Este campo é obrigatório."],
    "password": ["Este campo é obrigatório."]
  }
}
```

---

### 2. Redefinir Senha no Primeiro Acesso
**POST** `/api/auth/password/first-access-change/`

**Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
```

**Request:**
```json
{
  "new_password": "nova_senha_segura_123",
  "confirm_password": "nova_senha_segura_123"
}
```

**Response (Sucesso - 200):**
```json
{
  "status": "success",
  "data": null
}
```

**Response (Erro - senhas não conferem - 400):**
```json
{
  "status": "error",
  "message": "Dados inválidos",
  "errors": {
    "confirm_password": ["As senhas não conferem."]
  }
}
```

**Response (Erro - senha fraca - 400):**
```json
{
  "status": "error",
  "message": "Dados inválidos",
  "errors": {
    "new_password": [
      "Esta senha é muito curta. Ela precisa conter pelo menos 10 caracteres.",
      "A senha é muito similar ao nome de usuário.",
      "Esta senha é muito comum."
    ]
  }
}
```

**Response (Erro - usuário não precisa trocar senha - 403):**
```json
{
  "status": "error",
  "message": "Usuário não precisa trocar a senha",
  "errors": {
    "non_field_errors": ["Usuário não precisa trocar a senha"]
  }
}
```

**Response (Erro - não autenticado - 401):**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

### 3. Obter Dados do Usuário Autenticado
**GET** `/api/auth/me/`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (Sucesso - 200):**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "username": "usuario",
    "email": "user@example.com",
    "first_name": "Nome",
    "last_name": "Sobrenome",
    "is_superuser": false
  }
}
```

---

### 4. Renovar Token de Acesso
**POST** `/api/auth/token/refresh/`

**Headers:**
```
Content-Type: application/json
```

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (Sucesso - 200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## 💻 Exemplo de Implementação - JavaScript/TypeScript

### authService.js (ou authService.ts)

```javascript
const API_BASE_URL = 'http://localhost:8000';

/**
 * Faz login do usuário
 */
export const login = async (username, password) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    const data = await response.json();

    if (data.status === 'success') {
      // Salva os tokens e informações no localStorage
      localStorage.setItem('access_token', data.data.access);
      localStorage.setItem('refresh_token', data.data.refresh);
      localStorage.setItem('user', JSON.stringify(data.data.user));
      localStorage.setItem('require_password_change', String(data.data.require_password_change));

      return {
        success: true,
        requirePasswordChange: data.data.require_password_change,
        user: data.data.user,
      };
    }

    return {
      success: false,
      message: data.message,
      errors: data.errors,
    };
  } catch (error) {
    console.error('Erro no login:', error);
    return {
      success: false,
      message: 'Erro ao conectar com o servidor',
      errors: { network: error.message },
    };
  }
};

/**
 * Troca a senha no primeiro acesso
 */
export const changeFirstAccessPassword = async (newPassword, confirmPassword) => {
  try {
    const token = localStorage.getItem('access_token');

    if (!token) {
      return {
        success: false,
        message: 'Token de autenticação não encontrado',
        errors: { auth: 'Token não encontrado' },
      };
    }

    const response = await fetch(`${API_BASE_URL}/api/auth/password/first-access-change/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        new_password: newPassword,
        confirm_password: confirmPassword,
      }),
    });

    const data = await response.json();

    if (response.ok && data.status === 'success') {
      // Remove o flag de trocar senha
      localStorage.setItem('require_password_change', 'false');

      return {
        success: true,
      };
    }

    // Trata erros HTTP específicos
    if (response.status === 403) {
      return {
        success: false,
        message: data.message || 'Usuário não precisa trocar a senha',
        errors: data.errors,
      };
    }

    if (response.status === 401) {
      return {
        success: false,
        message: 'Sessão expirada. Faça login novamente.',
        errors: { auth: 'Token inválido ou expirado' },
      };
    }

    return {
      success: false,
      message: data.message || 'Erro ao trocar senha',
      errors: data.errors,
    };
  } catch (error) {
    console.error('Erro ao trocar senha:', error);
    return {
      success: false,
      message: 'Erro ao conectar com o servidor',
      errors: { network: error.message },
    };
  }
};

/**
 * Obtém informações do usuário autenticado
 */
export const getMe = async () => {
  try {
    const token = localStorage.getItem('access_token');

    const response = await fetch(`${API_BASE_URL}/api/auth/me/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    const data = await response.json();

    if (data.status === 'success') {
      return {
        success: true,
        user: data.data,
      };
    }

    return {
      success: false,
      message: data.message,
      errors: data.errors,
    };
  } catch (error) {
    return {
      success: false,
      message: 'Erro ao buscar dados do usuário',
      errors: error,
    };
  }
};

/**
 * Renova o token de acesso
 */
export const refreshToken = async () => {
  try {
    const refresh = localStorage.getItem('refresh_token');

    const response = await fetch(`${API_BASE_URL}/api/auth/token/refresh/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh }),
    });

    const data = await response.json();

    if (response.ok) {
      localStorage.setItem('access_token', data.access);
      return {
        success: true,
        access: data.access,
      };
    }

    return {
      success: false,
      message: 'Erro ao renovar token',
    };
  } catch (error) {
    return {
      success: false,
      message: 'Erro ao renovar token',
      errors: error,
    };
  }
};

/**
 * Faz logout do usuário
 */
export const logout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  localStorage.removeItem('require_password_change');
};

/**
 * Verifica se o usuário está autenticado
 */
export const isAuthenticated = () => {
  return !!localStorage.getItem('access_token');
};

/**
 * Verifica se o usuário precisa trocar a senha
 */
export const requiresPasswordChange = () => {
  return localStorage.getItem('require_password_change') === 'true';
};
```

---

## 🔄 Fluxo de Autenticação

### Fluxograma

```
┌─────────────────┐
│  Usuário tenta  │
│   fazer login   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│ POST /api/auth/login/           │
│ { username, password }          │
└────────┬───────────────┬────────┘
         │               │
    ✅ Sucesso      ❌ Erro (401)
         │               │
         ▼               ▼
┌──────────────────┐  ┌──────────────────┐
│ Salva tokens no  │  │ Exibe mensagem   │
│  localStorage    │  │ "Credenciais     │
└────────┬─────────┘  │  inválidas"      │
         │            └──────────────────┘
         ▼
┌─────────────────────────────────┐
│ require_password_change = true? │
└────────┬───────────────┬────────┘
         │               │
      ✅ Sim          ❌ Não
         │               │
         ▼               ▼
┌──────────────────┐  ┌──────────────────┐
│ Redireciona para │  │ Redireciona para │
│ tela de trocar   │  │   Dashboard      │
│     senha        │  └──────────────────┘
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Usuário define nova senha           │
│ POST /api/auth/password/            │
│      first-access-change/           │
│ { new_password, confirm_password }  │
└────────┬───────────────┬────────────┘
         │               │
    ✅ Sucesso      ❌ Erro (400)
         │               │
         ▼               ▼
┌──────────────────┐  ┌──────────────────┐
│ Marca flag como  │  │ Exibe erros de   │
│ false e          │  │ validação        │
│ redireciona para │  └──────────────────┘
│   Dashboard      │
└──────────────────┘
```

---

## ⚠️ Validações de Senha

O backend valida automaticamente usando os validadores do Django:

1. **MinimumLengthValidator(10)** - Mínimo de 10 caracteres
2. **UserAttributeSimilarityValidator** - Não pode ser similar ao username, email, etc.
3. **CommonPasswordValidator** - Não pode ser uma senha comum (ex: "password123")
4. **NumericPasswordValidator** - Não pode ser totalmente numérica

### Exemplo de Validação no Frontend (Opcional)

```javascript
const validatePassword = (password, username = '') => {
  const errors = [];

  if (password.length < 10) {
    errors.push('A senha deve ter no mínimo 10 caracteres');
  }

  if (/^\d+$/.test(password)) {
    errors.push('A senha não pode ser totalmente numérica');
  }

  if (username && password.toLowerCase().includes(username.toLowerCase())) {
    errors.push('A senha não pode conter seu nome de usuário');
  }

  // Lista de senhas comuns (simplificada)
  const commonPasswords = ['password', '12345678', 'qwerty', 'abc123'];
  if (commonPasswords.some(common => password.toLowerCase().includes(common))) {
    errors.push('Senha muito comum, escolha outra');
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
};
```

---

## 🛡️ Proteção de Rotas

### Exemplo de Guard/Middleware

```javascript
// utils/authGuard.js
import { isAuthenticated, requiresPasswordChange } from './authService';

export const requireAuth = (to, from, next) => {
  if (!isAuthenticated()) {
    // Redireciona para login se não estiver autenticado
    return next('/login');
  }

  // Se precisa trocar senha e não está indo para a página de trocar senha
  if (requiresPasswordChange() && to.path !== '/first-access-password-change') {
    return next('/first-access-password-change');
  }

  // Se não precisa trocar senha e está tentando acessar a página de trocar senha
  if (!requiresPasswordChange() && to.path === '/first-access-password-change') {
    return next('/dashboard');
  }

  next();
};
```

---

## 🧪 Testando com cURL

### 1. Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "teste", "password": "senha_temp123"}'
```

### 2. Trocar senha no primeiro acesso
```bash
# Substitua SEU_TOKEN pelo token recebido no login
curl -X POST http://localhost:8000/api/auth/password/first-access-change/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -d '{
    "new_password": "nova_senha_segura_123",
    "confirm_password": "nova_senha_segura_123"
  }'
```

### 3. Obter dados do usuário
```bash
curl -X GET http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer SEU_TOKEN"
```

---

## 📝 Notas Importantes

1. **CORS**: O backend deve ter CORS configurado para aceitar requisições do frontend
2. **HTTPS**: Em produção, sempre use HTTPS
3. **Token Refresh**: Implemente refresh automático de tokens para melhor UX
4. **Error Handling**: Trate todos os possíveis erros HTTP (400, 401, 403, 500)
5. **Loading States**: Mostre indicadores de carregamento durante as requisições
6. **Validação Client-Side**: Valide inputs no frontend antes de enviar para economizar requisições

---

## 🔗 Endpoints Adicionais

### Listar Usuários (Requer Autenticação)
**GET** `/api/auth/users/`

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "username": "usuario",
      "email": "user@example.com",
      "first_name": "Nome",
      "last_name": "Sobrenome"
    }
  ]
}
```

---

## 👥 Administração de Usuários (Requer Admin)

### ⚠️ IMPORTANTE: Endpoints Corretos

| Operação | Método | Endpoint Correto |
|----------|--------|------------------|
| Listar   | GET    | `/api/auth/admin/users/` |
| **Criar** | **POST** | **`/api/auth/admin/users/`** ⚠️ |
| Detalhes | GET    | `/api/auth/admin/users/{id}/` |
| Atualizar | PUT/PATCH | `/api/auth/admin/users/{id}/` |
| Deletar  | DELETE | `/api/auth/admin/users/{id}/` |

**❌ NÃO USE:** `/api/auth/users/` (apenas GET, não aceita POST)

---

### 1. Listar Usuários
**GET** `/api/auth/admin/users/`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "username": "usuario",
      "email": "user@example.com",
      "first_name": "Nome",
      "last_name": "Sobrenome"
    }
  ]
}
```

### 2. Criar Usuário
**POST** `/api/auth/admin/users/`

**Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
```

**Request:**
```json
{
  "username": "novo_usuario",
  "email": "novo@example.com",
  "password": "senha_temporaria_123",
  "first_name": "Nome",
  "last_name": "Sobrenome"
}
```

**Response (Sucesso - 201):**
```json
{
  "status": "success",
  "data": {
    "id": 2,
    "username": "novo_usuario",
    "email": "novo@example.com",
    "first_name": "Nome",
    "last_name": "Sobrenome"
  }
}
```

**Response (Erro - 400):**
```json
{
  "status": "error",
  "message": "Dados inválidos",
  "errors": {
    "username": ["Este nome de usuário já existe."]
  }
}
```

**Response (Erro - 403):**
```json
{
  "status": "error",
  "message": "Você não tem permissão para realizar essa ação.",
  "errors": {}
}
```

### 3. Obter Detalhes de um Usuário
**GET** `/api/auth/admin/users/{id}/`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "username": "usuario",
    "email": "user@example.com",
    "first_name": "Nome",
    "last_name": "Sobrenome"
  }
}
```

### 4. Atualizar Usuário
**PUT/PATCH** `/api/auth/admin/users/{id}/`

**Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
```

**Request (PUT - todos os campos):**
```json
{
  "username": "usuario_atualizado",
  "email": "atualizado@example.com",
  "first_name": "Nome Atualizado",
  "last_name": "Sobrenome Atualizado"
}
```

**Request (PATCH - campos parciais):**
```json
{
  "first_name": "Novo Nome"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "username": "usuario_atualizado",
    "email": "atualizado@example.com",
    "first_name": "Novo Nome",
    "last_name": "Sobrenome Atualizado"
  }
}
```

### 5. Deletar Usuário
**DELETE** `/api/auth/admin/users/{id}/`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "status": "success",
  "data": null
}
```

---

## 🔐 Gerenciamento de Senhas (Admin)

### 1. Alterar Própria Senha
**POST** `/api/auth/admin/users/password/change/`

**Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
```

**Request:**
```json
{
  "old_password": "senha_atual",
  "new_password": "nova_senha_segura_123",
  "confirm_password": "nova_senha_segura_123"
}
```

**Response:**
```json
{
  "status": "success",
  "data": null
}
```

### 2. Definir Senha de Outro Usuário (Admin)
**POST** `/api/auth/admin/users/{id}/password/set/`

**Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
```

**Request:**
```json
{
  "new_password": "senha_temporaria_123",
  "confirm_password": "senha_temporaria_123"
}
```

**Response:**
```json
{
  "status": "success",
  "data": null
}
```

**Nota:** Quando um admin define a senha de um usuário, o campo `require_password_change` é automaticamente marcado como `true`, forçando o usuário a trocar a senha no próximo login.

---

## 📝 Exemplo de Implementação - Criar Usuário

```javascript
// services/userService.js
const API_BASE_URL = 'http://localhost:8000';

export const createUser = async (userData) => {
  try {
    const token = localStorage.getItem('access_token');

    const response = await fetch(`${API_BASE_URL}/api/auth/admin/users/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        username: userData.username,
        email: userData.email,
        password: userData.password,
        first_name: userData.first_name || '',
        last_name: userData.last_name || '',
      }),
    });

    const data = await response.json();

    if (response.status === 201 && data.status === 'success') {
      return {
        success: true,
        user: data.data,
      };
    }

    if (response.status === 403) {
      return {
        success: false,
        message: 'Você não tem permissão de administrador',
        errors: data.errors,
      };
    }

    return {
      success: false,
      message: data.message || 'Erro ao criar usuário',
      errors: data.errors,
    };
  } catch (error) {
    console.error('Erro ao criar usuário:', error);
    return {
      success: false,
      message: 'Erro ao conectar com o servidor',
      errors: { network: error.message },
    };
  }
};
```

---

## 📚 Documentação Completa da API

Acesse: `http://localhost:8000/api/schema/swagger-ui/`

Ou baixe o schema OpenAPI: `http://localhost:8000/api/schema/`
