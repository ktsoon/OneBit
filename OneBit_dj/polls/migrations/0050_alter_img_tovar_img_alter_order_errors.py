# Generated by Django 5.0.3 on 2025-01-19 15:16

import django.core.validators
import polls.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0049_order_errors_alter_img_tovar_img_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='img_tovar',
            name='img',
            field=models.FileField(null=True, upload_to=polls.models.img_tovar, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'jfif', 'pjpeg', 'pjp', 'png', 'svg', 'webp', 'gif', 'avi', 'flv', 'mp4', 'mpg'])], verbose_name='Картинка или видео'),
        ),
        migrations.AlterField(
            model_name='order',
            name='errors',
            field=models.CharField(blank=True, default=None, help_text='Если возникла ошибка, то опишите её пользователю', max_length=250, null=True, verbose_name='Описать ошибку'),
        ),
    ]
