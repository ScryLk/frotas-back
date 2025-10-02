from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frotas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='carro',
            name='odometro_atual',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
