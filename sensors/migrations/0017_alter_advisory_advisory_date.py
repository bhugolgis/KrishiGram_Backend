# Generated by Django 4.1.6 on 2023-07-14 05:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sensors', '0016_alter_advisory_advisory_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advisory',
            name='Advisory_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
