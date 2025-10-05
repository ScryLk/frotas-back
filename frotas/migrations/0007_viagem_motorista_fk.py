from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('frotas', '0006_motorista_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='viagem',
            name='motorista',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='viagens', to='frotas.motorista'),
        ),
    ]
