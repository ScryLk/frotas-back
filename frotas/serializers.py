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
    tem_odometro = serializers.BooleanField(required=False, default=True)

    class Meta:
        model = Carro
        fields = ['placa', 'sem_placa', 'tem_odometro', 'modelo', 'secretaria', 'ano', 'ativo', 'odometro_atual', 'criado_em', 'atualizado_em']
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
        extra_kwargs = {
            'odometro_saida': {'required': False, 'allow_null': True},
            'odometro_chegada': {'required': False, 'allow_null': True},
        }

    def validate(self, attrs):
        carro = attrs.get('carro', getattr(self.instance, 'carro', None))

        # Se o carro não tem odômetro ou está sem placa, não valida odômetro
        if carro and hasattr(carro, 'tem_odometro') and not carro.tem_odometro:
            return attrs
        if carro and hasattr(carro, 'sem_placa') and carro.sem_placa:
            return attrs

        # Se está criando uma nova viagem e o carro TEM odômetro, odometro_saida é obrigatório
        if self.instance is None:  # Criando nova viagem
            odo_s = attrs.get('odometro_saida')
            if odo_s is None:
                raise serializers.ValidationError({
                    'odometro_saida': 'Este campo é obrigatório para carros com odômetro.'
                })
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
        # ✅ Só valida baseline do odometro_saida na CRIAÇÃO, não na edição
        if 'odometro_saida' in attrs and odo_s is not None:
            # Se está criando (instance é None), valida baseline
            if self.instance is None and odo_s < baseline:
                errors['odometro_saida'] = [f'Deve ser maior ou igual ao último odômetro registrado do carro ({baseline}).']

        if odo_c is not None:
            # Validação: odometro_chegada deve ser >= odometro_saida
            if odo_s is None:
                # considerar odometro_saida atual da instância para PATCH parcial
                ref_saida = getattr(self.instance, 'odometro_saida', None)
            else:
                ref_saida = odo_s
            if ref_saida is not None and odo_c < ref_saida:
                errors['odometro_chegada'] = ['Deve ser maior ou igual ao odômetro de saída.']

            # ✅ Só valida baseline do odometro_chegada na CRIAÇÃO, não na edição
            if self.instance is None and odo_c < baseline:
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
class ViagemCountDataSerializer(serializers.Serializer):
    count = serializers.IntegerField()


class ViagemCountResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = ViagemCountDataSerializer()


class ViagensTotaisDataSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    em_andamento = serializers.IntegerField()
    concluida = serializers.IntegerField()
    cancelada = serializers.IntegerField()
    km_total = serializers.IntegerField()
    duracao_media_min = serializers.IntegerField()


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


class ViagensTopCarrosKmItemSerializer(serializers.Serializer):
    placa = serializers.CharField()
    modelo = serializers.CharField()
    total_km = serializers.IntegerField()


class ViagensTopCarrosKmResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = ViagensTopCarrosKmItemSerializer(many=True)


class ViagemKmPorDiaItemSerializer(serializers.Serializer):
    data = serializers.DateField()
    total_km = serializers.IntegerField()
    total_viagens = serializers.IntegerField()


class ViagemKmPorDiaResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = ViagemKmPorDiaItemSerializer(many=True)
