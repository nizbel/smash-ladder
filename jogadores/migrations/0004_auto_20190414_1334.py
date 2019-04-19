# Generated by Django 2.2 on 2019-04-14 16:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jogadores', '0003_auto_20190414_1333'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='jogador',
            unique_together={('nick',)},
        ),
        migrations.AlterUniqueTogether(
            name='personagem',
            unique_together={('nome',)},
        ),
        migrations.AlterUniqueTogether(
            name='stage',
            unique_together={('nome', 'modelo')},
        ),
    ]
