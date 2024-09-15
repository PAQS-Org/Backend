from django.contrib import admin
from .models import ScanInfo, CheckoutInfo, LogProduct
# Register your models here.


admin.site.register(ScanInfo)
admin.site.register(CheckoutInfo)
admin.site.register(LogProduct)
