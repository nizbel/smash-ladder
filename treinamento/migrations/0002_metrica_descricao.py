# Generated by Django 2.2 on 2019-09-24 22:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('treinamento', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='metrica',
            name='descricao',
            field=models.CharField(default='', max_length=250, verbose_name='Descrição da métrica'),
            preserve_default=False,
        ),
    ]
