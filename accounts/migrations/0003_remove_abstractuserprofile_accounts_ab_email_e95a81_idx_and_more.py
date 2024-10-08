# Generated by Django 4.2.16 on 2024-09-29 01:17

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_abstractuserprofile_is_phone_verified_and_more'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='abstractuserprofile',
            name='accounts_ab_email_e95a81_idx',
        ),
        migrations.RemoveField(
            model_name='abstractuserprofile',
            name='phone_number',
        ),
        migrations.AddField(
            model_name='user',
            name='phone_number',
            field=models.CharField(blank=True, max_length=17, validators=[django.core.validators.RegexValidator(message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.", regex='^\\+?1?\\d{9,15}$')]),
        ),
        migrations.AddIndex(
            model_name='abstractuserprofile',
            index=models.Index(fields=['email'], name='accounts_ab_email_fbbb96_idx'),
        ),
    ]
