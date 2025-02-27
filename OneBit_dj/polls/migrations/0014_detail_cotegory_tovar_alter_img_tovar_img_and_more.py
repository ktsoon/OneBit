# Generated by Django 5.0.3 on 2024-05-06 16:16

import django.db.models.deletion
import polls.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0013_alter_avtor_slug_alter_category_slug_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='detail',
            name='cotegory_tovar',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='polls.category', verbose_name='Категория товара'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='img_tovar',
            name='img',
            field=models.FileField(null=True, upload_to=polls.models.img_tovar, verbose_name='Картинка или видео'),
        ),
        migrations.AlterField(
            model_name='tovars',
            name='skidka_cost',
            field=models.IntegerField(blank=True, help_text='можно оставить пустым', null=True, verbose_name='Ценна со скидкой'),
        ),
    ]
