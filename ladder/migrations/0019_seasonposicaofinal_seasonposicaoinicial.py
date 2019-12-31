# Generated by Django 2.2 on 2019-12-29 21:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jogadores', '0015_auto_20190918_1912'),
        ('ladder', '0018_lockdown'),
    ]

    operations = [
        migrations.CreateModel(
            name='SeasonPosicaoInicial',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('posicao', models.SmallIntegerField(verbose_name='Posição inicial')),
                ('jogador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jogadores.Jogador')),
                ('season', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='season_posicao_inicial', to='ladder.Season')),
            ],
            options={
                'unique_together': {('jogador', 'season'), ('posicao', 'season')},
            },
        ),
        migrations.CreateModel(
            name='SeasonPosicaoFinal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('posicao', models.SmallIntegerField(verbose_name='Posição final')),
                ('jogador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jogadores.Jogador')),
                ('season', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='season_posicao_final', to='ladder.Season')),
            ],
            options={
                'unique_together': {('jogador', 'season'), ('posicao', 'season')},
            },
        ),
    ]