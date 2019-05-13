# Generated by Django 2.2 on 2019-05-05 19:03

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ladder', '0003_auto_20190421_1756'),
    ]

    operations = [
        migrations.AddField(
            model_name='desafioladder',
            name='posicao_desafiado',
            field=models.SmallIntegerField(default=0, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Posição do desafiado'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='desafioladder',
            name='posicao_desafiante',
            field=models.SmallIntegerField(default=0, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Posição do desafiante'),
            preserve_default=False,
        ),
    ]
