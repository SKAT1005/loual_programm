# Generated by Django 5.0.6 on 2024-07-27 23:23

import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_alter_cart_product_alter_cart_stocks_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Название категории')),
            ],
        ),
        migrations.AlterField(
            model_name='user',
            name='last_lottery_time',
            field=models.DateTimeField(default=datetime.datetime(2024, 7, 26, 2, 23, 31, 73879), verbose_name='Последняя дата использования лотереи'),
        ),
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.category', verbose_name='Категория'),
        ),
    ]
