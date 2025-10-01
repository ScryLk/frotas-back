from django.contrib import admin
from .models import Secretaria, Carro, Usuario, Viagem


@admin.register(Secretaria)
class SecretariaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'responsavel', 'criado_em', 'atualizado_em')
    search_fields = ('nome', 'responsavel')


@admin.register(Carro)
class CarroAdmin(admin.ModelAdmin):
    list_display = ('placa', 'modelo', 'secretaria', 'ano', 'ativo')
    list_filter = ('ativo', 'secretaria')
    search_fields = ('placa', 'modelo')


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'nome', 'email', 'ativo', 'origem_ad')
    list_filter = ('ativo', 'origem_ad')
    search_fields = ('username', 'nome', 'email')


@admin.register(Viagem)
class ViagemAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'secretaria', 'carro', 'motorista', 'destino',
        'data_saida', 'odometro_saida', 'data_chegada', 'odometro_chegada', 'em_andamento'
    )
    list_filter = ('secretaria', 'carro', 'motorista')
    search_fields = ('destino', 'observacoes')
