# Guia de Implementação - Redefinição de Senha no Primeiro Acesso

## 📋 Resumo
Este guia explica como implementar a funcionalidade de redefinição de senha obrigatória no primeiro acesso no frontend.

## 🔐 Como Funciona

Quando um usuário faz login pela primeira vez (ou quando um admin cria uma conta), o backend retorna um campo adicional `require_password_change: true` na resposta do login. O frontend deve detectar isso e redirecionar o usuário para uma tela de redefinição de senha.

---

## 📡 API Endpoints

### 1. Login
**POST** `/api/auth/login/`

**Request:**
```json
{
  "username": "usuario",
  "password": "senha123"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "require_password_change": true,  // ⚠️ NOVO CAMPO
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

### 2. Redefinir Senha no Primeiro Acesso
**POST** `/api/auth/password/first-access-change/`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request:**
```json
{
  "new_password": "nova_senha_segura_123",
  "confirm_password": "nova_senha_segura_123"
}
```

**Response (Sucesso):**
```json
{
  "status": "success",
  "data": null
}
```

**Response (Erro - senhas não conferem):**
```json
{
  "status": "error",
  "message": "Dados inválidos",
  "errors": {
    "confirm_password": ["As senhas não conferem."]
  }
}
```

**Response (Erro - usuário não precisa trocar senha):**
```json
{
  "status": "error",
  "message": "Usuário não precisa trocar a senha",
  "errors": {
    "non_field_errors": ["Usuário não precisa trocar a senha"]
  }
}
```

---

## 💻 Implementação Frontend

### Passo 1: Modificar o Serviço de Login

```javascript
// services/authService.js
export const login = async (username, password) => {
  try {
    const response = await fetch('/api/auth/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    const data = await response.json();

    if (data.status === 'success') {
      // Salva os tokens
      localStorage.setItem('access_token', data.data.access);
      localStorage.setItem('refresh_token', data.data.refresh);
      localStorage.setItem('user', JSON.stringify(data.data.user));

      // ⚠️ IMPORTANTE: Salva se precisa trocar senha
      localStorage.setItem('require_password_change', data.data.require_password_change);

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
    return {
      success: false,
      message: 'Erro ao fazer login',
      errors: error,
    };
  }
};

export const changeFirstAccessPassword = async (newPassword, confirmPassword) => {
  try {
    const token = localStorage.getItem('access_token');

    const response = await fetch('/api/auth/password/first-access-change/', {
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

    if (data.status === 'success') {
      // ⚠️ Remove o flag de trocar senha
      localStorage.setItem('require_password_change', 'false');

      return {
        success: true,
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
      message: 'Erro ao trocar senha',
      errors: error,
    };
  }
};
```

### Passo 2: Criar Componente de Redefinição de Senha

```jsx
// components/FirstAccessPasswordChange.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { changeFirstAccessPassword } from '../services/authService';

const FirstAccessPasswordChange = () => {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validação básica
    if (newPassword.length < 10) {
      setError('A senha deve ter no mínimo 10 caracteres');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('As senhas não conferem');
      return;
    }

    setLoading(true);

    const result = await changeFirstAccessPassword(newPassword, confirmPassword);

    setLoading(false);

    if (result.success) {
      alert('Senha alterada com sucesso!');
      navigate('/dashboard'); // Redireciona para a página principal
    } else {
      // Exibe erros do backend
      if (result.errors && result.errors.confirm_password) {
        setError(result.errors.confirm_password[0]);
      } else if (result.errors && result.errors.new_password) {
        setError(result.errors.new_password[0]);
      } else {
        setError(result.message || 'Erro ao trocar senha');
      }
    }
  };

  return (
    <div className="first-access-container">
      <div className="first-access-card">
        <h2>🔐 Primeiro Acesso</h2>
        <p>Por favor, defina uma nova senha para continuar</p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="newPassword">Nova Senha</label>
            <input
              type="password"
              id="newPassword"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Mínimo 10 caracteres"
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirmar Senha</label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Digite a senha novamente"
              required
              disabled={loading}
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" disabled={loading}>
            {loading ? 'Alterando...' : 'Alterar Senha'}
          </button>
        </form>

        <div className="password-requirements">
          <p><strong>Requisitos da senha:</strong></p>
          <ul>
            <li>Mínimo de 10 caracteres</li>
            <li>Não pode ser muito similar ao seu nome de usuário</li>
            <li>Não pode ser uma senha muito comum</li>
            <li>Não pode ser totalmente numérica</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default FirstAccessPasswordChange;
```

### Passo 3: Modificar o Fluxo de Login

```jsx
// pages/Login.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../services/authService';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await login(username, password);

    setLoading(false);

    if (result.success) {
      // ⚠️ VERIFICA SE PRECISA TROCAR SENHA
      if (result.requirePasswordChange) {
        navigate('/first-access-password-change');
      } else {
        navigate('/dashboard');
      }
    } else {
      setError(result.message || 'Erro ao fazer login');
    }
  };

  return (
    <div className="login-container">
      <form onSubmit={handleSubmit}>
        <h2>Login</h2>

        <input
          type="text"
          placeholder="Usuário"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          disabled={loading}
        />

        <input
          type="password"
          placeholder="Senha"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          disabled={loading}
        />

        {error && <div className="error">{error}</div>}

        <button type="submit" disabled={loading}>
          {loading ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
    </div>
  );
};

export default Login;
```

### Passo 4: Adicionar Rota no React Router

```jsx
// App.jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import FirstAccessPasswordChange from './components/FirstAccessPasswordChange';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />

        {/* Rota protegida para trocar senha no primeiro acesso */}
        <Route
          path="/first-access-password-change"
          element={
            <ProtectedRoute>
              <FirstAccessPasswordChange />
            </ProtectedRoute>
          }
        />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

### Passo 5: Proteger Rotas (Opcional mas Recomendado)

```jsx
// components/ProtectedRoute.jsx
import React from 'react';
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('access_token');
  const requirePasswordChange = localStorage.getItem('require_password_change') === 'true';

  // Se não está autenticado, redireciona para login
  if (!token) {
    return <Navigate to="/login" />;
  }

  // Se precisa trocar senha e não está na página de trocar senha, redireciona
  const isOnPasswordChangePage = window.location.pathname === '/first-access-password-change';
  if (requirePasswordChange && !isOnPasswordChangePage) {
    return <Navigate to="/first-access-password-change" />;
  }

  return children;
};

export default ProtectedRoute;
```

---

## 🎨 CSS de Exemplo

```css
/* styles/FirstAccessPasswordChange.css */
.first-access-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.first-access-card {
  background: white;
  padding: 40px;
  border-radius: 10px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  max-width: 500px;
  width: 100%;
}

.first-access-card h2 {
  margin-bottom: 10px;
  color: #333;
}

.first-access-card > p {
  color: #666;
  margin-bottom: 30px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
}

.form-group input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 16px;
  transition: border-color 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.form-group input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.error-message {
  background-color: #fee;
  color: #c33;
  padding: 12px;
  border-radius: 5px;
  margin-bottom: 20px;
  border-left: 4px solid #c33;
}

button[type="submit"] {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 5px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}

button[type="submit"]:hover {
  transform: translateY(-2px);
}

button[type="submit"]:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.password-requirements {
  margin-top: 30px;
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 5px;
  border-left: 4px solid #667eea;
}

.password-requirements p {
  margin: 0 0 10px 0;
  color: #333;
}

.password-requirements ul {
  margin: 0;
  padding-left: 20px;
  color: #666;
}

.password-requirements li {
  margin-bottom: 5px;
}
```

---

## 🧪 Testando a Implementação

### 1. Criar Usuário de Teste no Backend
```bash
python manage.py shell -c "
from django.contrib.auth.models import User
user = User.objects.create_user('teste', 'teste@example.com', 'senha_temporaria123')
print(f'Usuário criado: {user.username}')
print(f'Precisa trocar senha: {user.profile.require_password_change}')
"
```

### 2. Testar Fluxo no Frontend
1. Acesse a página de login
2. Entre com:
   - Usuário: `teste`
   - Senha: `senha_temporaria123`
3. Você deve ser redirecionado automaticamente para `/first-access-password-change`
4. Defina uma nova senha (mínimo 10 caracteres)
5. Após trocar, você será redirecionado para o dashboard
6. Em próximos logins, não será mais solicitado trocar a senha

---

## ⚠️ Validações da Senha

O backend valida automaticamente:
- ✅ Mínimo de 10 caracteres
- ✅ Não pode ser muito similar ao nome de usuário
- ✅ Não pode ser uma senha muito comum (ex: "password123")
- ✅ Não pode ser totalmente numérica

Se houver erro de validação, o backend retorna:
```json
{
  "status": "error",
  "message": "Dados inválidos",
  "errors": {
    "new_password": ["A senha é muito similar ao nome de usuário."]
  }
}
```

---

## 📝 Notas Importantes

1. **Segurança**: O endpoint de trocar senha requer autenticação JWT
2. **Usuários Existentes**: Usuários criados antes desta funcionalidade têm `require_password_change = False` por padrão
3. **Novos Usuários**: Todos os novos usuários criados terão `require_password_change = True` automaticamente
4. **Admin**: Admins podem criar usuários e eles terão que trocar a senha no primeiro login

---

## 🔄 Fluxograma

```
Login
  ↓
Autenticação OK?
  ↓ Sim
require_password_change == true?
  ↓ Sim                    ↓ Não
Redireciona para         Redireciona para
trocar senha             Dashboard
  ↓
Usuário define nova senha
  ↓
Marca require_password_change = false
  ↓
Redireciona para Dashboard
```

---

## 📞 Suporte

Se tiver dúvidas ou problemas, verifique:
1. Console do navegador para erros JavaScript
2. Network tab para verificar as requisições HTTP
3. Logs do Django para erros no backend
4. Se o token JWT está sendo enviado corretamente no header Authorization
