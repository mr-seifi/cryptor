# Generated by Django 4.0.5 on 2022-06-07 10:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0006_historicaluser_cap_user_cap'),
        ('exchange', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kucoin',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='kucoin', to='account.user'),
        ),
    ]
