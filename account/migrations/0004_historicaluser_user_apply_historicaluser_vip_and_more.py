# Generated by Django 4.0.5 on 2022-06-04 21:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_historicaltrader_historicaluser_remove_trader_wallet_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaluser',
            name='user_apply',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='historicaluser',
            name='vip',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='user_apply',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='vip',
            field=models.BooleanField(default=False),
        ),
    ]