from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frotas', '0002_add_odometro_atual'),
    ]

    operations = [
        migrations.AlterField(
            model_name='carro',
            name='odometro_atual',
            field=models.PositiveIntegerField(null=True, blank=True, default=None),
        ),
    ]
