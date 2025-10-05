from django.contrib import admin
from .models import Secretaria, Carro, Motorista, Viagem


@admin.register(Secretaria)
class SecretariaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'responsavel', 'criado_em', 'atualizado_em')
    search_fields = ('nome', 'responsavel')


@admin.register(Carro)
class CarroAdmin(admin.ModelAdmin):
    list_display = ('placa', 'modelo', 'secretaria', 'ano', 'ativo')
    list_filter = ('ativo', 'secretaria')
    search_fields = ('placa', 'modelo')


@admin.register(Motorista)
class MotoristaAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)


@admin.register(Viagem)
class ViagemAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'secretaria', 'carro', 'motorista', 'destino',
        'data_saida', 'odometro_saida', 'data_chegada', 'odometro_chegada', 'em_andamento'
    )
    list_filter = ('secretaria', 'carro', 'motorista')
    search_fields = ('destino',)
