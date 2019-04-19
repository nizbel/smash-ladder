# Generated by Django 2.2 on 2019-04-15 04:38

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ladder', '0007_auto_20190414_2320'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registroladder',
            name='score_desafiado',
            field=models.SmallIntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(3)], verbose_name='Vitórias do desafiado'),
        ),
        migrations.AlterField(
            model_name='registroladder',
            name='score_desafiante',
            field=models.SmallIntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(3)], verbose_name='Vitórias do desafiante'),
        ),
    ]
