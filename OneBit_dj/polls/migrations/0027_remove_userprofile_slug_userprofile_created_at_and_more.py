# Generated by Django 5.0.3 on 2024-06-06 16:02

import django.core.validators
import polls.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0026_alter_img_tovar_img_userprofile'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='slug',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='created_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Дата'),
        ),
        migrations.AlterField(
            model_name='img_tovar',
            name='img',
            field=models.FileField(null=True, upload_to=polls.models.img_tovar, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'jfif', 'pjpeg', 'pjp', 'png', 'svg', 'webp', 'gif', 'avi', 'flv', 'mp4', 'mpg'])], verbose_name='Картинка или видео'),
        ),
    ]
