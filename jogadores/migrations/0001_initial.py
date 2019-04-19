# Generated by Django 2.2 on 2019-04-14 05:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Personagem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=30, verbose_name='Nome')),
            ],
        ),
        migrations.CreateModel(
            name='Jogador',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nick', models.CharField(max_length=30, verbose_name='Nickname')),
                ('admin', models.BooleanField(default=False, verbose_name='É da administração?')),
                ('ultimo_uso_corinda', models.DateTimeField(blank=True, default=None, null=True, verbose_name='Último uso de coringa')),
                ('main', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='jogadores.Personagem')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
