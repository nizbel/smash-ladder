# Generated by Django 2.2 on 2019-09-29 20:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configuracao', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuracaoladder',
            name='melhor_de',
            field=models.SmallIntegerField(default=5, verbose_name='Limite máximo de partidas em um desafio'),
        ),
        migrations.AlterField(
            model_name='configuracaoladder',
            name='limite_posicoes_desafio',
            field=models.SmallIntegerField(default=3, verbose_name='Limite de posições para desafiar'),
        ),
        migrations.AlterField(
            model_name='historicoconfiguracaoladder',
            name='limite_posicoes_desafio',
            field=models.SmallIntegerField(blank=True, null=True, verbose_name='Limite de posições para desafiar'),
        ),
    ]
