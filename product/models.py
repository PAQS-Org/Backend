from django.db import models
from accounts.models import Company, User
import string
import random
import re
from django.core.cache import cache

class ProductsInfo(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    company_name = models.ForeignKey(to=Company, on_delete=models.CASCADE, related_name="companyInfo")
    batch_number = models.CharField(max_length=120)
    product_name = models.CharField(max_length=50)
    perishable = models.BooleanField(default=False)
    manufacture_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    render_type = models.CharField(max_length=120)
    checkout = models.BooleanField(default=False)
    reference_id = models.PositiveIntegerField(unique=True, null=False, blank=False)
    patch = models.BooleanField(default=False)
    patch_message = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        indexes = [
            models.Index(fields=['reference_id'])
        ]
    
    def generate_unique_product_code(self):
        while True:
            code = random.randint(00, 99)
            if not ProductsInfo.objects.filter(reference_id=code).exists():
                return code
    
    def save(self, *args, **kwargs):
        if not self.reference_id:
            self.reference_id = self.generate_unique_product_code()
        super().save(*args, **kwargs)

# Concentrate on the generating of the codes. When you are done, then you come to this. do not over think.
class ScanInfo(models.Model):
   date_time = models.DateField(auto_now_add=True)
   code_key = models.CharField(max_length=255, blank=False, null=False)
   company_name = models.CharField(max_length=255, blank=False, null=False)
   product_name = models.CharField(max_length=255, blank=False, null=False)
   batch_number = models.CharField(max_length=255, blank=False, null=False)
   user_name = models.CharField(max_length=255)
   location = models.JSONField()
   country = models.CharField(max_length=255, blank=True, null=True)
   region = models.CharField(max_length=255, blank=True, null=True)
   city = models.CharField(max_length=255, blank=True, null=True)
   town = models.CharField(max_length=255, blank=True, null=True)
   street = models.CharField(max_length=255, blank=True, null=True)
   
   class Meta:
        indexes = [
            models.Index(fields=['company_name', 'product_name', 'batch_number', 'code_key' ])
        ]
        unique_together = ('code_key', 'company_name', 'product_name', 'batch_number', 'user_name')

class CheckoutInfo(models.Model):
   date_time = models.DateField(auto_now_add=True)
   code_key = models.CharField(max_length=255, blank=False, null=False)
   company_name = models.CharField(max_length=255, blank=False, null=False)
   product_name = models.CharField(max_length=255, blank=False, null=False)
   batch_number = models.CharField(max_length=255, blank=False, null=False)
   user_name = models.CharField(max_length=255)
   location = models.JSONField()
   country = models.CharField(max_length=255, blank=True, null=True)
   region = models.CharField(max_length=255, blank=True, null=True)
   city = models.CharField(max_length=255, blank=True, null=True)
   town = models.CharField(max_length=255, blank=True, null=True)
   street = models.CharField(max_length=255, blank=True, null=True)
   
   class Meta:
        indexes = [
            models.Index(fields=['company_name', 'product_name', 'batch_number', 'code_key' ])
        ]
        unique_together = ('code_key', 'company_name', 'product_name', 'batch_number', 'user_name')


class LogProduct(models.Model):
    company_name = models.CharField(max_length=100)
    product_name = models.CharField(max_length=100)
    batch_number = models.CharField(max_length=50)
    code_key = models.CharField(max_length=300)
    perishable = models.CharField(max_length=100)
    manufacture_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    message = models.CharField(max_length=255)
    checkout_user_email = models.EmailField(max_length=200, blank=True, null=True)
    checkout_user_phone = models.PositiveBigIntegerField(blank=True, null=True)
    checkout = models.BooleanField(default=False)
    checkout_message = models.CharField(max_length=255)
    patch = models.BooleanField(default=False)
    patch_message = models.CharField(max_length=255)

    class Meta:
        db_table = 'LogProduct'
        managed = True
        verbose_name = 'Logproduct'
        verbose_name_plural = 'Logproducts'
        indexes = [
            models.Index(fields=['code_key', 'company_name', 'product_name', 'batch_number'])
        ]

    def __str__(self):
        return f"{self.company_name}-{self.product_name}-{self.batch_number}"

    def __unicode__(self):
        return self.code_key
    
    def save(self, *args, **kwargs):
        # Invalidate or update the cache if patch or checkout changes
        if self.pk:
            # Fetch the previous state of the object
            previous = LogProduct.objects.get(pk=self.pk)
            if previous.patch != self.patch or previous.checkout != self.checkout:
                cache_key = sanitize_cache_key(f"log_product_{self.company_name}_{self.product_name}_{self.batch_number}_{self.code_key}")
                cache.delete(cache_key)
        
        super().save(*args, **kwargs)


def sanitize_cache_key(key):
    return re.sub(r'[^A-Za-z0-9_]', '_', key)