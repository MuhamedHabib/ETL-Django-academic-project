# Generated by Django 3.0.5 on 2022-03-19 10:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0002_customer_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='email',
            field=models.CharField(default='', max_length=100),
        ),
    ]
