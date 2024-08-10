# Generated by Django 5.0.6 on 2024-08-10 09:20

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0001_initial'),
    ]

    operations = [
        migrations.RenameIndex(
            model_name='logproduct',
            new_name='LogProduct_qr_key_fc91bc_idx',
            old_name='LogProduct_qr_key_af7ecf_idx',
        ),
        migrations.AddField(
            model_name='logproduct',
            name='expiry_date',
            field=models.CharField(default=django.utils.timezone.now, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='logproduct',
            name='manufacture_date',
            field=models.CharField(default=django.utils.timezone.now, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='logproduct',
            name='perishable',
            field=models.CharField(default=False, max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='logproduct',
            name='company_code',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='logproduct',
            name='product_code',
            field=models.CharField(max_length=100),
        ),
    ]
