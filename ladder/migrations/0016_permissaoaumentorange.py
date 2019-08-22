# Generated by Django 2.2 on 2019-08-13 16:03

from django.db import migrations, models
import django.db.models.deletion
import smashLadder.utils


class Migration(migrations.Migration):

    dependencies = [
        ('jogadores', '0014_feedback'),
        ('ladder', '0015_resultadoremocaojogador'),
    ]

    operations = [
        migrations.CreateModel(
            name='PermissaoAumentoRange',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_hora', smashLadder.utils.DateTimeFieldTz(verbose_name='Data e hora da permissão')),
                ('admin_permissor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='permissor_aumento_range', to='jogadores.Jogador')),
                ('jogador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='permitido_aumento_range', to='jogadores.Jogador')),
            ],
        ),
    ]