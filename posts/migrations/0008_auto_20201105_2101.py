# Generated by Django 2.2.6 on 2020-11-05 17:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_auto_20201105_2059'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='text',
            field=models.TextField(max_length=280),
        ),
    ]
