# filepath: frotas/management/commands/setup_operador.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from frotas.models import Localizacao

class Command(BaseCommand):
    help = "Cria/atualiza o grupo 'Operador' com permissões de Localização e (opcional) adiciona usuários ao grupo."

    def add_arguments(self, parser):
        parser.add_argument('--user', action='append', dest='users', default=[], help='Username a ser adicionado ao grupo Operador (pode repetir).')
        parser.add_argument('--create-user', action='store_true', dest='create_user', help='Cria o usuário se não existir (senha padrão: oper123).')

    def handle(self, *args, **options):
        grp, _ = Group.objects.get_or_create(name='Operador')
        ct = ContentType.objects.get_for_model(Localizacao)
        needed = ['add_localizacao', 'change_localizacao', 'delete_localizacao', 'view_localizacao']
        perms = Permission.objects.filter(content_type=ct, codename__in=needed)
        existing = set(grp.permissions.values_list('codename', flat=True))
        for p in perms:
            if p.codename not in existing:
                grp.permissions.add(p)
        grp.save()
        self.stdout.write(self.style.SUCCESS("Grupo 'Operador' atualizado com permissões: " + ", ".join(needed)))

        users = options.get('users') or []
        create_user = options.get('create_user')
        for username in users:
            user, created = User.objects.get_or_create(username=username)
            if created and create_user:
                user.set_password('oper123')
                user.is_staff = False
                user.is_superuser = False
                user.save()
                self.stdout.write(self.style.WARNING(f"Usuário '{username}' criado com senha padrão 'oper123'."))
            user.groups.add(grp)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Usuário '{username}' associado ao grupo 'Operador'."))

        self.stdout.write(self.style.SUCCESS('Concluído.'))
