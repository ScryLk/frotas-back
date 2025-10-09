# Solução: Erros 500 nos Endpoints da API

## ❌ Problema

O frontend está recebendo erros 500 ao acessar endpoints como:
- `/api/viagens/totais/`
- `/api/viagens/km_por_secretaria/`
- `/api/viagens/top_destinos/`
- `/api/relatorios/totais/`
- `/api/relatorios/km_por_secretaria/`
- `/api/relatorios/top_destinos/`

## 🔍 Causa Raiz

Os endpoints do **ViagemViewSet** (linhas 238-289) estão configurados com:
```python
@action(detail=False, methods=['get'], url_path='totais', permission_classes=[permissions.IsAuthenticated])
```

Isso significa que **requerem autenticação**, mas o frontend está fazendo requisições **sem o token JWT**.

## ✅ Soluções

### Solução 1: Enviar Token nas Requisições (Recomendado)

O frontend deve enviar o token de autenticação em **todas as requisições**:

```javascript
// services/api.js ou similar
const API_BASE_URL = 'http://localhost:8000';

const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};

export const fetchViagensTotal = async () => {
  const response = await fetch(`${API_BASE_URL}/api/viagens/totais/`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return await response.json();
};
```

#### Se estiver usando Axios:

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

// Interceptor para adicionar token automaticamente
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const fetchViagensTotal = () => api.get('/api/viagens/totais/');
```

---

### Solução 2: Remover Autenticação dos Endpoints (Não Recomendado)

Se você **realmente** quer que esses endpoints sejam públicos (sem autenticação):

**Opção A:** Remover `permission_classes` dos endpoints

```python
# frotas/views.py - ViagemViewSet

@extend_schema(summary='Totais de viagens', tags=['Relatórios'])
@action(detail=False, methods=['get'], url_path='totais')  # ← Removido permission_classes
def totais(self, request):
    qs = self._period_filter(self.get_queryset(), request)
    # ... resto do código
```

**Opção B:** Usar `AllowAny` explicitamente

```python
from rest_framework.permissions import AllowAny

@action(detail=False, methods=['get'], url_path='totais', permission_classes=[AllowAny])
def totais(self, request):
    # ... código
```

⚠️ **Atenção:** Isso expõe os dados publicamente. Use apenas se for intencional.

---

### Solução 3: Usar os Endpoints do RelatoriosViewSet

O `RelatoriosViewSet` **não tem autenticação configurada** (ainda). Use:

- `/api/relatorios/totais/` em vez de `/api/viagens/totais/`
- `/api/relatorios/km_por_secretaria/` em vez de `/api/viagens/km_por_secretaria/`
- `/api/relatorios/top_destinos/` em vez de `/api/viagens/top_destinos/`

Mas **adicione autenticação** ao RelatoriosViewSet também:

```python
# frotas/views.py

class RelatoriosViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]  # ← Adicione isso

    @extend_schema(summary='Totais de viagens')
    @action(detail=False, methods=['get'], url_path='totais')
    def totais(self, request):
        # ... código
```

---

## 🔐 Melhor Prática: Proteger Todos os Endpoints

Adicione autenticação global no settings.py:

```python
# core/settings.py

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',  # ← Requer autenticação por padrão
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    # ... outras configurações
}
```

Depois, **explicitamente** marque endpoints públicos com `AllowAny`:

```python
from rest_framework.permissions import AllowAny

class PublicViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]  # Endpoint público
```

---

## 🧪 Testando

### 1. Obter token de autenticação

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "sua_senha"}'
```

Resposta:
```json
{
  "status": "success",
  "data": {
    "access": "eyJ0eXAiOiJKV1Qi...",
    "refresh": "eyJ0eXAiOiJKV1Qi..."
  }
}
```

### 2. Testar endpoint com token

```bash
curl -X GET http://localhost:8000/api/viagens/totais/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1Qi..."
```

Deve retornar 200 com os dados.

### 3. Testar sem token (deve retornar 401)

```bash
curl -X GET http://localhost:8000/api/viagens/totais/
```

Deve retornar 401 Unauthorized.

---

## 📝 Checklist de Correção

- [ ] **Frontend:** Verificar se o token está sendo salvo no localStorage após login
- [ ] **Frontend:** Adicionar header `Authorization: Bearer {token}` em todas as requisições
- [ ] **Frontend:** Implementar refresh de token quando expirar
- [ ] **Backend:** Confirmar que `permission_classes` está configurado corretamente
- [ ] **Backend:** Testar endpoints com e sem autenticação
- [ ] **Logs:** Verificar console do navegador para erros de autenticação

---

## 🚀 Implementação Rápida - Frontend com Axios

```javascript
// api.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

// Interceptor: Adiciona token automaticamente
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

// Interceptor: Trata erros de autenticação
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expirado, tentar refresh
      const refreshToken = localStorage.getItem('refresh_token');

      if (refreshToken) {
        try {
          const { data } = await axios.post('http://localhost:8000/api/auth/token/refresh/', {
            refresh: refreshToken
          });

          localStorage.setItem('access_token', data.access);

          // Retry request original
          error.config.headers.Authorization = `Bearer ${data.access}`;
          return axios(error.config);
        } catch (refreshError) {
          // Refresh falhou, redirecionar para login
          localStorage.clear();
          window.location.href = '/login';
        }
      } else {
        // Sem refresh token, redirecionar para login
        localStorage.clear();
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export default api;

// Uso:
// import api from './api';
// const response = await api.get('/api/viagens/totais/');
```

---

## 📊 Status Atual dos Endpoints

| Endpoint | ViewSet | Autenticação | Status |
|----------|---------|--------------|--------|
| `/api/viagens/totais/` | ViagemViewSet | ✅ Required | 401 sem token |
| `/api/viagens/km_por_secretaria/` | ViagemViewSet | ✅ Required | 401 sem token |
| `/api/viagens/top_destinos/` | ViagemViewSet | ✅ Required | 401 sem token |
| `/api/relatorios/totais/` | RelatoriosViewSet | ❌ None | Público (provavelmente não intencional) |
| `/api/relatorios/km_por_secretaria/` | RelatoriosViewSet | ❌ None | Público (provavelmente não intencional) |
| `/api/relatorios/top_destinos/` | RelatoriosViewSet | ❌ None | Público (provavelmente não intencional) |

**Recomendação:** Adicione autenticação ao `RelatoriosViewSet` e configure o frontend para enviar tokens.
