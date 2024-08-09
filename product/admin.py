from django.contrib import admin
from .models import ProductsInfo, ScanInfo, CheckoutInfo, LogProduct
# Register your models here.

admin.site.register(ProductsInfo)
admin.site.register(ScanInfo)
admin.site.register(CheckoutInfo)
admin.site.register(LogProduct)
