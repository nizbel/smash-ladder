# Generated by Django 2.2 on 2019-12-29 20:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ladder', '0016_permissaoaumentorange'),
    ]

    operations = [
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ano', models.SmallIntegerField(verbose_name='Ano')),
                ('indice', models.SmallIntegerField(verbose_name='Índice da Season')),
                ('data_inicio', models.DateField(verbose_name='Data de início')),
                ('data_fim', models.DateField(verbose_name='Data de fim')),
            ],
        ),
    ]
