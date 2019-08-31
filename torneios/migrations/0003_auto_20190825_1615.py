# Generated by Django 2.2 on 2019-08-25 19:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('torneios', '0002_auto_20190822_1353'),
    ]

    operations = [
        migrations.RenameField(
            model_name='jogadortorneio',
            old_name='id_no_torneio',
            new_name='id_challonge',
        ),
        migrations.AddField(
            model_name='torneio',
            name='id_challonge',
            field=models.IntegerField(default=0, verbose_name='Código de identificação no torneio'),
            preserve_default=False,
        ),
    ]
