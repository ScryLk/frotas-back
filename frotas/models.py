import uuid
from django.db import models


class TimeStampedModel(models.Model):
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Secretaria(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=120, unique=True)
    responsavel = models.CharField(max_length=120, blank=True, null=True)

    class Meta:
        verbose_name = 'Secretaria'
        verbose_name_plural = 'Secretarias'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Carro(TimeStampedModel):
    placa = models.CharField(primary_key=True, max_length=10)
    modelo = models.CharField(max_length=120)
    secretaria = models.ForeignKey(Secretaria, on_delete=models.PROTECT, related_name='carros')
    ano = models.PositiveIntegerField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    odometro_atual = models.PositiveIntegerField(null=True, blank=True, default=None)

    class Meta:
        verbose_name = 'Carro'
        verbose_name_plural = 'Carros'
        ordering = ['placa']

    def __str__(self):
        return f"{self.placa} - {self.modelo}"


class Motorista(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=120)

    class Meta:
        verbose_name = 'Motorista'
        verbose_name_plural = 'Motoristas'
        ordering = ['nome']
        db_table = 'frotas_motorista'

    def __str__(self):
        return self.nome


class Viagem(TimeStampedModel):
    class Status(models.TextChoices):
        EM_ANDAMENTO = 'em_andamento', 'Em andamento'
        CONCLUIDA = 'concluida', 'Concluída'
        CANCELADA = 'cancelada', 'Cancelada'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    secretaria = models.ForeignKey(Secretaria, on_delete=models.PROTECT, related_name='viagens')
    carro = models.ForeignKey(Carro, to_field='placa', db_column='carro_placa', on_delete=models.PROTECT, related_name='viagens')
    motorista = models.ForeignKey(Motorista, on_delete=models.PROTECT, related_name='viagens')
    data_saida = models.DateTimeField()
    odometro_saida = models.PositiveIntegerField()
    data_chegada = models.DateTimeField(blank=True, null=True)
    odometro_chegada = models.PositiveIntegerField(blank=True, null=True)
    destino = models.CharField(max_length=160)
    observacoes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.EM_ANDAMENTO)

    class Meta:
        verbose_name = 'Viagem'
        verbose_name_plural = 'Viagens'
        ordering = ['-data_saida']

    def __str__(self):
        return f"Viagem {self.id} - {self.carro_id} para {self.destino}"

    @property
    def em_andamento(self):
        return self.status == self.Status.EM_ANDAMENTO

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Atualiza odômetro do carro ao salvar viagem (tratando nulos como 0 para baseline)
        try:
            carro = self.carro
            target = self.odometro_chegada or self.odometro_saida
            baseline = carro.odometro_atual or 0
            if target is not None and target > baseline:
                carro.odometro_atual = target
                carro.save(update_fields=['odometro_atual', 'atualizado_em'])
        except Exception:
            # Evita quebrar a persistência da viagem por erro secundário
            pass
