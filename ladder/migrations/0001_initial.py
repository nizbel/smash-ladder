# Generated by Django 2.2 on 2019-04-19 23:24

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('jogadores', '0007_auto_20190417_0226'),
    ]

    operations = [
        migrations.CreateModel(
            name='DesafioLadder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('desafio_coringa', models.BooleanField(verbose_name='É desafio coringa?')),
                ('score_desafiante', models.SmallIntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(3)], verbose_name='Vitórias do desafiante')),
                ('score_desafiado', models.SmallIntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(3)], verbose_name='Vitórias do desafiado')),
                ('data_hora', models.DateTimeField(verbose_name='Data e hora do resultado')),
                ('adicionado_por', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='criador_registro', to='jogadores.Jogador')),
                ('admin_validador', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='admin_validador', to='jogadores.Jogador')),
                ('desafiado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='desafiado', to='jogadores.Jogador')),
                ('desafiante', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='desafiante', to='jogadores.Jogador')),
            ],
            options={
                'unique_together': {('desafiante', 'desafiado', 'data_hora')},
            },
        ),
        migrations.CreateModel(
            name='Luta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.DateField(verbose_name='Data da luta')),
                ('adicionada_por', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='criador_luta', to='jogadores.Jogador')),
                ('ganhador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ganhador_luta', to='jogadores.Jogador')),
                ('stage', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='jogadores.Stage')),
            ],
        ),
        migrations.CreateModel(
            name='CancelamentoDesafioLadder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_hora', models.DateTimeField(auto_now_add=True, verbose_name='Data/hora da exclusão')),
                ('desafio_ladder', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='ladder.DesafioLadder')),
                ('jogador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jogadores.Jogador')),
            ],
        ),
        migrations.CreateModel(
            name='PosicaoLadder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('posicao', models.SmallIntegerField(verbose_name='Posição atual')),
                ('jogador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jogadores.Jogador')),
            ],
            options={
                'unique_together': {('posicao', 'jogador')},
            },
        ),
        migrations.CreateModel(
            name='LutaLadder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('indice_desafio_ladder', models.SmallIntegerField(verbose_name='Índice da luta')),
                ('desafio_ladder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ladder.DesafioLadder')),
                ('luta', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='ladder.Luta')),
            ],
            options={
                'ordering': ('indice_desafio_ladder',),
                'unique_together': {('desafio_ladder', 'indice_desafio_ladder'), ('desafio_ladder', 'luta')},
            },
        ),
        migrations.CreateModel(
            name='JogadorLuta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('jogador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jogadores.Jogador')),
                ('luta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ladder.Luta')),
                ('personagem', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='jogadores.Personagem')),
            ],
            options={
                'unique_together': {('jogador', 'luta')},
            },
        ),
        migrations.CreateModel(
            name='InicioLadder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('posicao', models.SmallIntegerField(verbose_name='Posição inicial')),
                ('jogador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jogadores.Jogador')),
            ],
            options={
                'unique_together': {('posicao', 'jogador')},
            },
        ),
        migrations.CreateModel(
            name='HistoricoLadder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mes', models.SmallIntegerField(verbose_name='Mês')),
                ('ano', models.SmallIntegerField(verbose_name='Ano')),
                ('posicao', models.SmallIntegerField(verbose_name='Posição no mês')),
                ('jogador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jogadores.Jogador')),
            ],
            options={
                'unique_together': {('jogador', 'mes', 'ano'), ('posicao', 'mes', 'ano')},
            },
        ),
    ]
