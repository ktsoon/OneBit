# Generated by Django 5.0.3 on 2025-01-19 13:25

import django.core.validators
import polls.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0047_order_tovars_user_alter_img_tovar_img'),
    ]

    operations = [
        migrations.AddField(
            model_name='order_tovars',
            name='t_cost',
            field=models.IntegerField(default=0, verbose_name='Цена'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='img_tovar',
            name='img',
            field=models.FileField(null=True, upload_to=polls.models.img_tovar, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'jfif', 'pjpeg', 'pjp', 'png', 'svg', 'webp', 'gif', 'avi', 'flv', 'mp4', 'mpg'])], verbose_name='Картинка или видео'),
        ),
    ]
