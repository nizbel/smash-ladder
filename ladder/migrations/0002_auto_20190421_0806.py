# Generated by Django 2.2 on 2019-04-21 11:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ladder', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='desafioladder',
            name='adicionado_por',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='criador_desafio', to='jogadores.Jogador'),
        ),
    ]
