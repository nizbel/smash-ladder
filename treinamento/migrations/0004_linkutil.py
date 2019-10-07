# Generated by Django 2.2 on 2019-10-07 03:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jogadores', '0015_auto_20190918_1912'),
        ('treinamento', '0003_auto_20190928_0358'),
    ]

    operations = [
        migrations.CreateModel(
            name='LinkUtil',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=30, verbose_name='Nome')),
                ('url', models.URLField(verbose_name='URL')),
                ('descricao', models.CharField(blank=True, max_length=250, null=True, verbose_name='Descrição do link')),
                ('jogador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jogadores.Jogador')),
            ],
        ),
    ]