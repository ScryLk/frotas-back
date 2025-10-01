from django.core.management.base import BaseCommand
from django.db.models import Max
from frotas.models import Carro


class Command(BaseCommand):
    help = "Atualiza o campo odometro_atual dos carros com base nas viagens existentes"

    def handle(self, *args, **options):
        updated = 0
        for carro in Carro.objects.all():
            latest = carro.viagens.aggregate(
                maior_odometro=Max('odometro_chegada'),
                maior_saida=Max('odometro_saida'),
            )
            target = max(
                (latest.get('maior_odometro') or 0),
                (latest.get('maior_saida') or 0)
            )
            if target and target > (carro.odometro_atual or 0):
                carro.odometro_atual = target
                carro.save(update_fields=['odometro_atual', 'atualizado_em'])
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"Carros atualizados: {updated}"))
