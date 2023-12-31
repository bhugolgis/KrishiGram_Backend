# Generated by Django 4.2 on 2023-06-28 10:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sensors', '0010_alter_advisory_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advisory',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='devices',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='layers',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='soilsensor',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='weathersensor',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
