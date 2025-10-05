from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frotas', '0004_usuario_somente_nome'),
    ]

    operations = [
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
    ]
