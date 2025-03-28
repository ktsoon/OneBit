# Generated by Django 5.0.3 on 2024-04-16 13:29

import polls.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0004_gl_category_alter_img_tovar_img_category_gl_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='category',
            field=models.CharField(db_index=True, help_text='Введите название категории', max_length=120, unique=True, verbose_name='Категория'),
        ),
        migrations.AlterField(
            model_name='gl_category',
            name='Gl_category',
            field=models.CharField(db_index=True, help_text='Введите название главной категории', max_length=120, unique=True, verbose_name='Главная категория'),
        ),
        migrations.AlterField(
            model_name='img_tovar',
            name='img',
            field=models.ImageField(null=True, upload_to=polls.models.img_tovar, verbose_name='Картинка'),
        ),
    ]
