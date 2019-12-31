# Generated by Django 2.2 on 2019-12-30 03:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ladder', '0019_seasonposicaofinal_seasonposicaoinicial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='season',
            name='data_fim',
            field=models.DateField(blank=True, null=True, verbose_name='Data de fim'),
        ),
        migrations.AlterUniqueTogether(
            name='season',
            unique_together={('ano', 'indice'), ('data_fim',), ('data_inicio',)},
        ),
    ]