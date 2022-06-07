# Generated by Django 4.0.5 on 2022-06-07 10:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0005_historicaluser_strategy_user_strategy'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaluser',
            name='cap',
            field=models.FloatField(max_length=5, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='cap',
            field=models.FloatField(max_length=5, null=True),
        ),
    ]