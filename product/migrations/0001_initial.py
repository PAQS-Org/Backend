# Generated by Django 5.0.6 on 2024-08-08 22:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0003_company_company_code_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductsInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('batch_number', models.CharField(max_length=7)),
                ('product_name', models.CharField(max_length=50)),
                ('perishable', models.BooleanField(default=False)),
                ('manufacture_date', models.DateField(blank=True, null=True)),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('render_type', models.CharField(max_length=7)),
                ('checkout', models.BooleanField(default=False)),
                ('reference_id', models.PositiveIntegerField(unique=True)),
                ('patch', models.BooleanField(default=False)),
                ('patch_message', models.CharField(blank=True, max_length=255, null=True)),
                ('company_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='companyInfo', to='accounts.company')),
            ],
            options={
                'verbose_name': 'Product',
                'verbose_name_plural': 'Products',
            },
        ),
        migrations.CreateModel(
            name='LogProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('batch_code', models.CharField(max_length=50)),
                ('qr_key', models.CharField(max_length=100)),
                ('message', models.CharField(max_length=100)),
                ('checkout', models.BooleanField(default=False)),
                ('checkout_message', models.CharField(max_length=100)),
                ('patch', models.BooleanField(default=False)),
                ('patch_message', models.CharField(max_length=100)),
                ('company_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logCompany', to='accounts.company')),
                ('product_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.productsinfo')),
            ],
            options={
                'verbose_name': 'Logproduct',
                'verbose_name_plural': 'Logproducts',
                'db_table': 'LogProduct',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='CheckoutInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code_key', models.CharField(max_length=255)),
                ('location', models.CharField(max_length=255)),
                ('country', models.CharField(max_length=255)),
                ('region', models.CharField(max_length=255)),
                ('city', models.CharField(max_length=255)),
                ('town', models.CharField(blank=True, max_length=255, null=True)),
                ('street', models.CharField(blank=True, max_length=255, null=True)),
                ('company_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checkoutCompany', to='accounts.company')),
                ('user_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.user')),
                ('product_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.productsinfo')),
            ],
        ),
        migrations.CreateModel(
            name='ScanInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code_key', models.CharField(max_length=255)),
                ('location', models.CharField(max_length=255)),
                ('country', models.CharField(max_length=255)),
                ('region', models.CharField(max_length=255)),
                ('city', models.CharField(max_length=255)),
                ('town', models.CharField(blank=True, max_length=255, null=True)),
                ('street', models.CharField(blank=True, max_length=255, null=True)),
                ('company_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scanCompany', to='accounts.company')),
                ('product_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.productsinfo')),
                ('user_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.user')),
            ],
        ),
        migrations.AddIndex(
            model_name='productsinfo',
            index=models.Index(fields=['reference_id'], name='product_pro_referen_5881c2_idx'),
        ),
        migrations.AddIndex(
            model_name='logproduct',
            index=models.Index(fields=['qr_key', 'company_code', 'product_code'], name='LogProduct_qr_key_af7ecf_idx'),
        ),
    ]
