# Generated by Django 2.2 on 2019-09-28 06:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('treinamento', '0002_metrica_descricao'),
    ]

    operations = [
        migrations.AlterField(
            model_name='metrica',
            name='descricao',
            field=models.CharField(blank=True, max_length=250, null=True, verbose_name='Descrição da métrica'),
        ),
    ]