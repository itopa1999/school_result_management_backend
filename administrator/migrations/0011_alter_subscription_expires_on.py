# Generated by Django 5.1.6 on 2025-06-05 21:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0010_alter_subscription_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='expires_on',
            field=models.DateField(blank=True, null=True),
        ),
    ]
