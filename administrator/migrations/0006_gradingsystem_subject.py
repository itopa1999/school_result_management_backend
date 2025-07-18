# Generated by Django 5.1.6 on 2025-05-22 10:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0005_result_termtotalmark_alter_academicsession_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='GradingSystem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('min_score', models.PositiveIntegerField()),
                ('max_score', models.PositiveIntegerField()),
                ('grade', models.CharField(max_length=2)),
                ('remark', models.CharField(max_length=255)),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='school_grading_system', to='administrator.schoolprofile')),
            ],
            options={
                'ordering': ['-min_score'],
            },
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='class_subjects', to='administrator.schoolprofile')),
            ],
            options={
                'ordering': ['-id'],
                'indexes': [models.Index(fields=['-name'], name='administrat_name_c0d937_idx')],
            },
        ),
    ]
