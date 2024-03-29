# Generated by Django 4.0.5 on 2022-06-07 07:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0004_historicaluser_user_apply_historicaluser_vip_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaluser',
            name='strategy',
            field=models.CharField(choices=[('low', 'LOW'), ('medium', 'MEDIUM'), ('high', 'HIGH')], default='low', max_length=8),
        ),
        migrations.AddField(
            model_name='user',
            name='strategy',
            field=models.CharField(choices=[('low', 'LOW'), ('medium', 'MEDIUM'), ('high', 'HIGH')], default='low', max_length=8),
        ),
    ]
