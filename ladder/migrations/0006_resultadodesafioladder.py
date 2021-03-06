# Generated by Django 2.2 on 2019-05-06 06:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jogadores', '0011_stagevalidaladder'),
        ('ladder', '0005_auto_20190505_1604'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResultadoDesafioLadder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('progresso', models.SmallIntegerField(verbose_name='Progresso na ladder após desafio')),
                ('desafio_ladder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ladder.DesafioLadder')),
                ('jogador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jogadores.Jogador')),
            ],
            options={
                'unique_together': {('desafio_ladder', 'jogador')},
            },
        ),
    ]
