from rest_framework import serializers
from .models import Secretaria, Carro, Viagem, Motorista, Localizacao
from django.db.models import Max


class SecretariaViagensCountItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    nome = serializers.CharField()
    total_viagens = serializers.IntegerField()


class SecretariaViagensCountResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = SecretariaViagensCountItemSerializer(many=True)


# Novos serializers para contagem de carros por secretaria
class SecretariaCarrosCountItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    nome = serializers.CharField()
    total_carros = serializers.IntegerField()


class SecretariaCarrosCountResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = SecretariaCarrosCountItemSerializer(many=True)


class SecretariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Secretaria
        fields = ['id', 'nome', 'responsavel', 'criado_em', 'atualizado_em']
        read_only_fields = ['id', 'criado_em', 'atualizado_em']


class CarroSerializer(serializers.ModelSerializer):
    odometro_atual = serializers.IntegerField(required=False, allow_null=True)
    sem_placa = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = Carro
        fields = ['placa', 'sem_placa', 'modelo', 'secretaria', 'ano', 'ativo', 'odometro_atual', 'criado_em', 'atualizado_em']
        read_only_fields = ['criado_em', 'atualizado_em']

    def create(self, validated_data):
        # Aceita 'odometro_atual' somente na criação via payload
        raw = self.initial_data.get('odometro_atual', None)
        if raw is not None:
            try:
                value = int(raw)
            except (TypeError, ValueError):
                raise serializers.ValidationError({'odometro_atual': 'Deve ser um inteiro maior ou igual a 0.'})
            if value < 0:
                raise serializers.ValidationError({'odometro_atual': 'Deve ser maior ou igual a 0.'})
            validated_data['odometro_atual'] = value
        return super().create(validated_data)

    def validate_odometro_atual(self, value):
        if value is None:
            return None
        if not isinstance(value, int):
            raise serializers.ValidationError('Deve ser um número inteiro >= 0')
        if value < 0:
            raise serializers.ValidationError('Deve ser um número inteiro >= 0')
        return value

    def validate(self, attrs):
        if attrs.get('sem_placa'):
            # se sem_placa, tornar placa opcional (gera placeholder se vazio)
            placa = attrs.get('placa') or ''
            if not placa:
                # gera identificador temporário (cliente pode editar depois)
                import uuid
                attrs['placa'] = f"TMP-{uuid.uuid4().hex[:6].upper()}"
        else:
            if not attrs.get('placa'):
                raise serializers.ValidationError({'placa': 'Obrigatória quando sem_placa=False.'})
        return attrs


class ViagemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Viagem
        fields = [
            'id', 'secretaria', 'carro', 'motorista', 'localizacao',
            'data_saida', 'odometro_saida',
            'data_chegada', 'odometro_chegada',
            'destino', 'observacoes', 'status',
            'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']

    def validate(self, attrs):
        data_saida = attrs.get('data_saida', getattr(self.instance, 'data_saida', None))
        data_chegada = attrs.get('data_chegada', getattr(self.instance, 'data_chegada', None))
        odo_s = attrs.get('odometro_saida', getattr(self.instance, 'odometro_saida', None))
        odo_c = attrs.get('odometro_chegada', getattr(self.instance, 'odometro_chegada', None))
        carro = attrs.get('carro', getattr(self.instance, 'carro', None))

        # validação de datas
        if data_chegada and data_saida and data_chegada < data_saida:
            raise serializers.ValidationError({'data_chegada': 'Deve ser maior ou igual à data de saída.'})

        # baseline de odômetro pelo histórico do carro
        if carro is not None:
            qs = Viagem.objects.filter(carro=carro)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            agg = qs.aggregate(max_saida=Max('odometro_saida'), max_chegada=Max('odometro_chegada'))
            historico_max = max(agg.get('max_saida') or 0, agg.get('max_chegada') or 0)
            baseline = max(historico_max, getattr(carro, 'odometro_atual', 0) or 0)
        else:
            baseline = 0

        errors = {}

        # validação de odômetros
        if odo_s is not None and odo_s < baseline:
            errors['odometro_saida'] = [f'Deve ser maior ou igual ao último odômetro registrado do carro ({baseline}).']

        if odo_c is not None:
            # já há verificação geral abaixo, mas reforçamos baseline também para chegada
            if odo_s is None:
                # considerar odometro_saida atual da instância para PATCH parcial
                ref_saida = getattr(self.instance, 'odometro_saida', None)
            else:
                ref_saida = odo_s
            if ref_saida is not None and odo_c < ref_saida:
                errors['odometro_chegada'] = ['Deve ser maior ou igual ao odômetro de saída.']
            if odo_c < baseline:
                errors.setdefault('odometro_chegada', []).append(f'Deve ser maior ou igual ao último odômetro registrado do carro ({baseline}).')

        if errors:
            raise serializers.ValidationError(errors)

        return attrs


class LocalizacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Localizacao
        fields = ['id', 'nome', 'endereco', 'descricao', 'latitude', 'longitude', 'criado_em', 'atualizado_em']
        read_only_fields = ['id', 'criado_em', 'atualizado_em']


# Envelopes para documentação e padronização de respostas
class SecretariaResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = SecretariaSerializer()


class SecretariaListResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = SecretariaSerializer(many=True)


class CarroResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = CarroSerializer()


class CarroListResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = CarroSerializer(many=True)


class ViagemResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = ViagemSerializer()


class ViagemListResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = ViagemSerializer(many=True)


# Motoristas
class MotoristaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Motorista
        fields = ['id', 'nome', 'criado_em', 'atualizado_em']
        read_only_fields = ['id', 'criado_em', 'atualizado_em']


class MotoristaResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = MotoristaSerializer()


class MotoristaListResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = MotoristaSerializer(many=True)


class LocalizacaoResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = LocalizacaoSerializer()


class LocalizacaoListResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = LocalizacaoSerializer(many=True)


# Relatórios / Analytics
class ViagensTotaisDataSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    em_andamento = serializers.IntegerField()
    concluida = serializers.IntegerField()
    cancelada = serializers.IntegerField()


class ViagensTotaisResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = ViagensTotaisDataSerializer()


class ViagensSerieItemSerializer(serializers.Serializer):
    periodo = serializers.CharField()
    total = serializers.IntegerField()


class ViagensSerieResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = ViagensSerieItemSerializer(many=True)


class ViagensKmPorSecretariaItemSerializer(serializers.Serializer):
    secretaria = serializers.UUIDField()
    nome = serializers.CharField()
    total_km = serializers.IntegerField()


class ViagensKmPorSecretariaResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = ViagensKmPorSecretariaItemSerializer(many=True)


class ViagensTopDestinosItemSerializer(serializers.Serializer):
    destino = serializers.CharField()
    total = serializers.IntegerField()


class ViagensTopDestinosResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = ViagensTopDestinosItemSerializer(many=True)
