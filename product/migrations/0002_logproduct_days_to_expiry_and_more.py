# Generated by Django 4.2.16 on 2024-09-16 12:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='logproduct',
            name='days_to_expiry',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='checkoutinfo',
            name='location',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='scaninfo',
            name='location',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
