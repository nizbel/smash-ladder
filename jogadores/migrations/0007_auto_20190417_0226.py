# Generated by Django 2.2 on 2019-04-17 05:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jogadores', '0006_registroferias'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='jogador',
            options={'ordering': ('nick',), 'verbose_name_plural': 'jogadores'},
        ),
        migrations.AlterModelOptions(
            name='personagem',
            options={'ordering': ('nome',), 'verbose_name_plural': 'personagens'},
        ),
        migrations.AlterModelOptions(
            name='stage',
            options={'ordering': ('nome', 'modelo')},
        ),
    ]
