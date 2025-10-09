# ✅ Problema dos Erros 500 - RESOLVIDO

## 🔍 Problema Original

O frontend estava recebendo erros 500 ao acessar endpoints como:
- `/api/viagens/totais/`
- `/api/viagens/km_por_secretaria/`
- `/api/viagens/top_destinos/`
- `/api/relatorios/*`

## 🎯 Causa Raiz Identificada

O erro **real** (não era 401, era 500) era:
```
Unknown column 'frotas_viagem.status' in 'field list'
```

### Migrations Não Aplicadas

As migrations `0012_viagem_status` e `0013_localizacao_viagem_localizacao` estavam pendentes:

```bash
$ python manage.py showmigrations frotas
frotas
 [X] 0011_alter_viagem_carro
 [ ] 0012_viagem_status          ← FALTANDO
 [ ] 0013_localizacao_viagem_localizacao  ← FALTANDO
```

## ✅ Solução Aplicada

### 1. Aplicada Migration 0012
```bash
python manage.py migrate frotas 0012
```
- ✅ Adicionou coluna `status` na tabela `frotas_viagem`

### 2. Criada Tabela `frotas_localizacao` Manualmente

A migration 0013 usava `SeparateDatabaseAndState` assumindo que a tabela já existia, mas ela não existia!

**SQL executado:**
```sql
CREATE TABLE IF NOT EXISTS `frotas_localizacao` (
  `id` char(32) NOT NULL PRIMARY KEY,
  `criado_em` datetime(6) NOT NULL,
  `atualizado_em` datetime(6) NOT NULL,
  `nome` varchar(160) NOT NULL,
  `endereco` varchar(255) DEFAULT NULL,
  `descricao` text,
  `latitude` decimal(9,6) DEFAULT NULL,
  `longitude` decimal(9,6) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE `frotas_viagem`
ADD COLUMN `localizacao_id` char(32) NULL,
ADD CONSTRAINT `frotas_viagem_localizacao_id_fk`
FOREIGN KEY (`localizacao_id`) REFERENCES `frotas_localizacao`(`id`);
```

### 3. Marcada Migration como Aplicada
```bash
python manage.py migrate frotas 0013 --fake
```

## 🧪 Teste de Validação

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# Resposta:
{
  "status": "success",
  "data": {
    "access": "eyJhbGci...",
    "refresh": "eyJhbGci..."
  }
}

# Testar endpoint COM token
curl "http://localhost:8000/api/viagens/totais/" \
  -H "Authorization: Bearer eyJhbGci..."

# Resposta:
{
  "status": "success",
  "data": {
    "total": 0,
    "em_andamento": 0,
    "concluida": 0,
    "cancelada": 0
  }
}
```

✅ **Status: 200 OK**

## 📝 O Que o Frontend Precisa Fazer

### 1. Fazer Login e Salvar Token

```javascript
const loginResponse = await fetch('http://localhost:8000/api/auth/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'admin' })
});

const { data } = await loginResponse.json();

// Salvar tokens
localStorage.setItem('access_token', data.access);
localStorage.setItem('refresh_token', data.refresh);
```

### 2. Enviar Token em TODAS as Requisições

```javascript
const token = localStorage.getItem('access_token');

const response = await fetch('http://localhost:8000/api/viagens/totais/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### 3. Configurar Axios com Interceptor (Recomendado)

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

// Adiciona token automaticamente em todas as requisições
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Uso:
const response = await api.get('/api/viagens/totais/');
```

## 🔐 Credenciais de Teste

- **Username:** `admin`
- **Password:** `admin`
- **is_superuser:** `true` (pode criar outros usuários)

## 📊 Status dos Endpoints

| Endpoint | Status | Autenticação | Resposta |
|----------|--------|--------------|----------|
| `/api/auth/login/` | ✅ OK | Não requerida | 200 |
| `/api/auth/password/first-access-change/` | ✅ OK | Requerida | 200 |
| `/api/auth/admin/users/` | ✅ OK | Admin required | 200 |
| `/api/viagens/totais/` | ✅ **CORRIGIDO** | Requerida | 200 |
| `/api/viagens/km_por_secretaria/` | ✅ **CORRIGIDO** | Requerida | 200 |
| `/api/viagens/top_destinos/` | ✅ **CORRIGIDO** | Requerida | 200 |
| `/api/relatorios/totais/` | ✅ **CORRIGIDO** | Requerida | 200 |

## 🚀 Próximos Passos

1. ✅ Backend: Migrations aplicadas
2. ✅ Backend: Tabelas criadas
3. ✅ Backend: Endpoints funcionando
4. ⏳ **Frontend: Implementar autenticação com tokens**
5. ⏳ Frontend: Adicionar interceptor para enviar tokens automaticamente
6. ⏳ Frontend: Implementar refresh de tokens quando expirarem

## 📚 Documentos de Referência

- [FRONTEND_API_GUIDE.md](FRONTEND_API_GUIDE.md) - Guia completo da API
- [FRONTEND_SINGLE_CARD_IMPLEMENTATION.md](FRONTEND_SINGLE_CARD_IMPLEMENTATION.md) - Implementação do card de login
- [FIX_500_ERRORS.md](FIX_500_ERRORS.md) - Guia de troubleshooting
- [SOLUCAO_PERMISSAO.md](SOLUCAO_PERMISSAO.md) - Como tornar usuários admin

## ✨ Resumo

**Antes:**
- ❌ Erro 500: `Unknown column 'frotas_viagem.status'`
- ❌ Migrations pendentes
- ❌ Tabelas faltando

**Depois:**
- ✅ Migrations aplicadas
- ✅ Tabelas criadas
- ✅ Endpoints retornando 200 OK
- ✅ Autenticação funcionando

**O frontend só precisa enviar o token JWT em todas as requisições!**
