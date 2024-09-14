from django_mongoengine.mongo_admin import DocumentAdmin
from django.contrib import admin
from .models import ScanInfo, CheckoutInfo, LogProduct
# Register your models here.

class ScanInfoAdmin(DocumentAdmin):
    list_display = ('company_name', 'product_name', 'batch_number', 'user_name', 'date_time')
    search_fields = ('company_name', 'product_name', 'batch_number')

class CheckoutInfoAdmin(DocumentAdmin):
    list_display = ('company_name', 'product_name', 'batch_number', 'user_name', 'date_time')
    search_fields = ('company_name', 'product_name', 'batch_number')

class LogProductInfoAdmin(DocumentAdmin):
    list_display = ('company_name', 'product_name', 'batch_number', 'user_name', 'date_time')
    search_fields = ('company_name', 'product_name', 'batch_number')


admin.site.register(ScanInfo, ScanInfoAdmin)
admin.site.register(CheckoutInfo, CheckoutInfoAdmin)
admin.site.register(LogProduct, LogProductInfoAdmin)
