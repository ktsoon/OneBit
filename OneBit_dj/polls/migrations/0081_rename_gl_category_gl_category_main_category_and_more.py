# Generated by Django 5.0.3 on 2025-03-13 19:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0080_alter_history_tovars_options'),
    ]

    operations = [
        migrations.RenameField(
            model_name='gl_category',
            old_name='Gl_category',
            new_name='main_category',
        ),
        migrations.RemoveField(
            model_name='category',
            name='Gl_category',
        ),
        migrations.AddField(
            model_name='category',
            name='main_categories',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='category', to='polls.gl_category', verbose_name='Главная категория'),
        ),
    ]
