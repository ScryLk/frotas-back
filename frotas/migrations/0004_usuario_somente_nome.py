from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frotas', '0003_make_odometro_nullable'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usuario',
            name='username',
        ),
        migrations.RemoveField(
            model_name='usuario',
            name='email',
        ),
        migrations.RemoveField(
            model_name='usuario',
            name='ativo',
        ),
        migrations.RemoveField(
            model_name='usuario',
            name='origem_ad',
        ),
        migrations.RunSQL(
            sql="UPDATE frotas_usuario SET nome = 'Sem nome' WHERE nome IS NULL;",
            reverse_sql="",
        ),
        migrations.AlterField(
            model_name='usuario',
            name='nome',
            field=models.CharField(max_length=120),
        ),
    ]
