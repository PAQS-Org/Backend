from django.db import models
import re
from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver
# Concentrate on the generating of the codes. When you are done, then you come to this. do not over think.
class ScanInfo(models.Model):
   date_time = models.DateTimeField(auto_now_add=True)
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
            models.Index(fields=['date_time','company_name', 'product_name', 'batch_number', 'code_key' ])
        ]

@receiver(post_save, sender=ScanInfo)
def invalidate_multiple_cache_keys(sender, instance, **kwargs):
    cache_keys = [
        f"scan_metrics_{instance.company_name}",
        f"user_scan_info_{instance.user_name}",
    ]
    for key in cache_keys:
        cache_key = sanitize_cache_key(key)
        cache.delete(cache_key) 


class CheckoutInfo(models.Model):
   date_time = models.DateTimeField(auto_now_add=True)
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
            models.Index(fields=['date_time','company_name', 'product_name', 'batch_number', 'code_key' ])
        ]

@receiver(post_save, sender=CheckoutInfo)
def invalidate_multiple_cache_keys(sender, instance, **kwargs):
    cache_keys = [
        f"checkout_metrics_{instance.company_name}",
        f"user_checkout_info_{instance.user_name}"
    ]
    
    # Invalidate all related cache keys
    for key in cache_keys:
        cache_key = sanitize_cache_key(key)
        cache.delete(cache_key) 


@receiver(post_save, sender=ScanInfo)
@receiver(post_save, sender=CheckoutInfo)
def invalidate_shared_cache(sender, instance, **kwargs):
    cache_keys = [
        f"location_metrics_comparison_{instance.company_name}",
        f"performance_metrics_{instance.company_name}",
        f"product_user_metrics_{instance.company_name}",
        f"line_chart_data_{instance.company_name}",
        f"product_metrics_{instance.company_name}_{instance.product_name}",
    ]
    
    # Invalidate all related cache keys
    for key in cache_keys:
        cache_key = sanitize_cache_key(key)
        cache.delete(cache_key) 


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
    patch_reason = models.CharField(max_length=100, blank=True, null=True)
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