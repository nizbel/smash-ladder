# Generated by Django 2.2 on 2019-04-14 05:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ladder', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registroladder',
            name='admin_validador',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='admin_validador', to='jogadores.Jogador'),
        ),
    ]
