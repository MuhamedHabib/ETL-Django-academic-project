# Generated by Django 3.0.5 on 2022-03-25 17:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backoffice', '0007_auto_20220324_1357'),
    ]

    operations = [
        migrations.AddField(
            model_name='car',
            name='serie',
            field=models.CharField(max_length=20, null=True),
        ),
    ]
