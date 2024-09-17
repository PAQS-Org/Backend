# Generated by Django 4.2.16 on 2024-09-17 00:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entry', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='keymanagement',
            name='aes_key',
        ),
        migrations.AddField(
            model_name='keymanagement',
            name='private_key',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='keymanagement',
            name='public_key',
            field=models.TextField(blank=True, null=True),
        ),
    ]
