# Generated by Django 4.2 on 2023-06-24 09:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sensors', '0007_rename_property_soilsensor_devices_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='devices',
            name='device_id',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='soilsensor',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
