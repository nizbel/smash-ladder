# Generated by Django 2.2 on 2019-05-28 16:06

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ladder', '0011_auto_20190528_1212'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='decaimentojogador',
            name='qtd_meses_inatividade',
        ),
        migrations.AddField(
            model_name='decaimentojogador',
            name='qtd_periodos_inatividade',
            field=models.SmallIntegerField(default=None, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(2)], verbose_name='Quantidade de períodos inativo'),
            preserve_default=False,
        ),
    ]
