from django.db import migrations


def ensure_table_rename_usuario_to_motorista(apps, schema_editor):
    connection = schema_editor.connection
    introspection = connection.introspection
    with connection.cursor() as cursor:
        existing_tables = set(introspection.table_names())
        usuario = 'frotas_usuario'
        motorista = 'frotas_motorista'

        usuario_exists = usuario in existing_tables
        motorista_exists = motorista in existing_tables

        # Se já temos a tabela final e não há a antiga, nada a fazer
        if motorista_exists and not usuario_exists:
            return

        # Se existe apenas a antiga, renomeia
        if usuario_exists and not motorista_exists:
            cursor.execute(f"RENAME TABLE `{usuario}` TO `{motorista}`;")
            return

        # Se existem as duas, tratamos o conflito
        if usuario_exists and motorista_exists:
            cursor.execute(f"SELECT COUNT(*) FROM `{motorista}`;")
            count_motorista = cursor.fetchone()[0]
            if count_motorista and int(count_motorista) > 0:
                # Evita perda de dados: não renomeia automaticamente
                return
            # Se a 'frotas_motorista' estiver vazia, podemos substituí-la
            cursor.execute(f"DROP TABLE `{motorista}`;")
            cursor.execute(f"RENAME TABLE `{usuario}` TO `{motorista}`;")


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('frotas', '0004_usuario_somente_nome'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(ensure_table_rename_usuario_to_motorista, noop_reverse),
            ],
            state_operations=[
                migrations.RenameModel(
                    old_name='Usuario',
                    new_name='Motorista',
                ),
                migrations.AlterModelOptions(
                    name='motorista',
                    options={
                        'verbose_name': 'Motorista',
                        'verbose_name_plural': 'Motoristas',
                        'ordering': ['nome'],
                    },
                ),
            ],
        ),
    ]
