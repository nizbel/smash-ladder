# Generated by Django 2.2 on 2019-04-16 17:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jogadores', '0006_registroferias'),
        ('ladder', '0010_cancelamentoregistroladder'),
    ]

    operations = [
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
    ]
