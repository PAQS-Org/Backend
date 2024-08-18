# Generated by Django 5.0.6 on 2024-08-18 16:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0005_alter_logproduct_checkout_message_and_more'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='logproduct',
            name='LogProduct_qr_key_fc91bc_idx',
        ),
        migrations.RenameField(
            model_name='logproduct',
            old_name='batch_code',
            new_name='batch_number',
        ),
        migrations.RenameField(
            model_name='logproduct',
            old_name='qr_key',
            new_name='code_key',
        ),
        migrations.RenameField(
            model_name='logproduct',
            old_name='company_code',
            new_name='company_name',
        ),
        migrations.RenameField(
            model_name='logproduct',
            old_name='product_code',
            new_name='product_name',
        ),
        migrations.AddIndex(
            model_name='logproduct',
            index=models.Index(fields=['code_key', 'company_name', 'product_name', 'batch_number'], name='LogProduct_code_ke_c7019e_idx'),
        ),
    ]
