# Generated by Django 2.2.16 on 2023-03-30 12:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_auto_20230326_1909'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, upload_to='posts/', verbose_name='Картинка'),
        ),
    ]
