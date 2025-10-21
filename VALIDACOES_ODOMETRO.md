# Validações de Odômetro - Sistema de Frotas

## Resumo das Validações Implementadas

### 1. Criação de Viagens (POST)

Ao **criar** uma nova viagem, as seguintes validações são aplicadas:

#### Odômetro de Saída:
- ✅ **Obrigatório** (se o carro tem odômetro)
- ✅ Deve ser **≥ baseline** (maior odômetro registrado anteriormente)
- ✅ O baseline é calculado como: `max(histórico de viagens, odometro_atual do carro)`

#### Odômetro de Chegada:
- ⚠️  Opcional (pode ser preenchido depois)
- ✅ Se preenchido, deve ser **≥ odometro_saida**
- ✅ Se preenchido, deve ser **≥ baseline**

### 2. Edição de Viagens (PATCH/PUT)

Ao **editar** uma viagem existente, as validações são mais flexíveis:

#### Odômetro de Saída:
- ✅ Pode ser editado (campo opcional no PATCH)
- ❌ **NÃO valida baseline** (permite correção de erros)
- ℹ️  Se não for enviado no request, mantém o valor atual

#### Odômetro de Chegada:
- ✅ Pode ser editado (campo opcional no PATCH)
- ✅ Deve ser **≥ odometro_saida** (da viagem atual)
- ❌ **NÃO valida baseline** (permite correção de erros)
- ℹ️  Se não for enviado no request, mantém o valor atual

## Exemplos

### ✅ Criando uma viagem (POST)

```json
POST /api/viagens/
{
  "carro": "CBC1323",
  "motorista": "uuid-motorista",
  "secretaria": "uuid-secretaria",
  "data_saida": "2025-10-21T08:00:00-03:00",
  "odometro_saida": 87500,  // ✅ Obrigatório, deve ser >= baseline
  "destino": "Prefeitura"
}
```

### ✅ Editando apenas a chegada (PATCH)

```json
PATCH /api/viagens/{id}/
{
  "data_chegada": "2025-10-21T10:00:00-03:00",
  "odometro_chegada": 87550  // ✅ Deve ser >= odometro_saida
}
```

**Nota:** Não é necessário reenviar `odometro_saida`!

### ✅ Corrigindo um erro de odômetro (PATCH)

```json
PATCH /api/viagens/{id}/
{
  "odometro_saida": 87400,  // ✅ Permitido mesmo se < baseline
  "odometro_chegada": 87450
}
```

**Nota:** Na edição, você pode corrigir erros de digitação sem a restrição de baseline.

## Validações que SEMPRE Acontecem

Independente de ser criação ou edição:

1. ✅ `odometro_chegada` deve ser `≥ odometro_saida`
2. ✅ `data_chegada` deve ser `≥ data_saida`
3. ✅ Carros sem odômetro (`tem_odometro: false`) não exigem odômetros
4. ✅ Carros sem placa (`sem_placa: true`) não exigem odômetros

## Arquivos de Código

- **Validações:** [frotas/serializers.py](frotas/serializers.py) (linhas 98-160)
- **Endpoints:** [frotas/views.py](frotas/views.py) (ViagemViewSet)

## Benefícios desta Abordagem

1. **Criação rigorosa:** Previne erros ao criar viagens com odômetros inválidos
2. **Edição flexível:** Permite corrigir erros de digitação sem bloqueios
3. **UX melhor:** Não precisa reenviar todos os campos ao editar
4. **Consistência:** Mantém validações lógicas (chegada >= saída)

## Testes Recomendados

### Teste 1: Criar viagem com odômetro baixo
```
POST /api/viagens/
odometro_saida: 1000 (mas último registro é 87500)
Resultado esperado: ❌ Erro de validação
```

### Teste 2: Editar viagem mudando apenas chegada
```
PATCH /api/viagens/{id}/
odometro_chegada: 87550
Resultado esperado: ✅ Sucesso (não valida baseline)
```

### Teste 3: Editar viagem corrigindo odômetro baixo
```
PATCH /api/viagens/{id}/
odometro_saida: 87400
Resultado esperado: ✅ Sucesso (permite correção)
```
