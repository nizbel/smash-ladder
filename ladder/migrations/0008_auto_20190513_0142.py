# Generated by Django 2.2 on 2019-05-13 04:42

from django.db import migrations, models
import smashLadder.utils


class Migration(migrations.Migration):

    dependencies = [
        ('ladder', '0007_auto_20190507_1236'),
    ]

    operations = [
        migrations.AlterField(
            model_name='desafioladder',
            name='data_hora',
            field=smashLadder.utils.DateTimeFieldTz(verbose_name='Data e hora do resultado'),
        ),
        migrations.AlterField(
            model_name='desafioladder',
            name='posicao_desafiado',
            field=models.SmallIntegerField(default=0, verbose_name='Posição do desafiado'),
        ),
        migrations.AlterField(
            model_name='desafioladder',
            name='posicao_desafiante',
            field=models.SmallIntegerField(default=0, verbose_name='Posição do desafiante'),
        ),
    ]
