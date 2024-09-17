from django.db import models
import re
from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver
from entry.models import KeyManagement
from PAQSBackend.encry import EncryptionUtil
# Concentrate on the generating of the codes. When you are done, then you come to this. do not over think.
class ScanInfo(models.Model):
   date_time = models.DateTimeField(auto_now_add=True)
   code_key = models.CharField(max_length=255, blank=False, null=False)
   company_name = models.CharField(max_length=255, blank=False, null=False)
   product_name = models.CharField(max_length=255, blank=False, null=False)
   batch_number = models.CharField(max_length=255, blank=False, null=False)
   user_name = models.CharField(max_length=255)
   location = models.JSONField(blank=True, null=True)
   country = models.CharField(max_length=255, blank=True, null=True)
   region = models.CharField(max_length=255, blank=True, null=True)
   city = models.CharField(max_length=255, blank=True, null=True)
   town = models.CharField(max_length=255, blank=True, null=True)
   street = models.CharField(max_length=255, blank=True, null=True)
   key_version=models.CharField(max_length=255, blank=True, null=True)
   
   class Meta:
        indexes = [
            models.Index(fields=['date_time','company_name', 'product_name', 'batch_number', 'code_key' ])
        ]
        
   def save(self, *args, **kwargs):
       current_key_obj = KeyManagement.get_current_key()
       if not current_key_obj:
            raise ValueError("No encryption key found in KeyManagement")
        
       current_key = current_key_obj.public_key
       current_version = current_key_obj.version           
       
       if not self.key_version:
           self.code_key = EncryptionUtil.encrypt(self.code_key, current_key)
           self.company_name = EncryptionUtil.encrypt(self.company_name, current_key)
           self.product_name = EncryptionUtil.encrypt(self.product_name, current_key)
           self.batch_number = EncryptionUtil.encrypt(self.batch_number, current_key)
           self.user_name = EncryptionUtil.encrypt(self.user_name, current_key)
           self.location = EncryptionUtil.encrypt(self.location, current_key) if self.location else None
           self.country = EncryptionUtil.encrypt(self.country, current_key) if self.country else None
           self.region = EncryptionUtil.encrypt(self.region, current_key) if self.region else None
           self.city = EncryptionUtil.encrypt(self.city, current_key) if self.city else None
           self.town = EncryptionUtil.encrypt(self.town, current_key) if self.town else None
           self.street = EncryptionUtil.encrypt(self.street, current_key) if self.street else None
           self.key_version = current_version
        
       else:
           if self.key_version < current_key:
                old_key = KeyManagement.get_key_by_version(self.key_version).private_key
                self.code_key = EncryptionUtil.rotate_key(self.code_key, old_key, current_key)
                self.company_name = EncryptionUtil.rotate_key(self.company_name, old_key, current_key)
                self.product_name = EncryptionUtil.rotate_key(self.product_name, old_key, current_key)
                self.batch_number = EncryptionUtil.rotate_key(self.batch_number, old_key, current_key)
                self.user_name = EncryptionUtil.rotate_key(self.user_name, old_key, current_key)
                self.location = EncryptionUtil.rotate_key(self.location, old_key, current_key) if self.location else None
                self.country = EncryptionUtil.rotate_key(self.country, old_key, current_key) if self.country else None
                self.region = EncryptionUtil.rotate_key(self.region, old_key, current_key) if self.region else None
                self.city = EncryptionUtil.rotate_key(self.city, old_key, current_key) if self.city else None
                self.town = EncryptionUtil.rotate_key(self.town, old_key, current_key) if self.town else None
                self.street = EncryptionUtil.rotate_key(self.street, old_key, current_key) if self.street else None 
                self.key_version = current_version
       
       
       cache_keys = [
            f"scan_metrics_{self.company_name}",
            f"user_scan_info_{self.user_name}",
        ]
        
        # Invalidate all related cache keys
       for key in cache_keys:
            cache_key = sanitize_cache_key(key)
            cache.delete(cache_key)
       super().save(*args, **kwargs)

class CheckoutInfo(models.Model):
   date_time = models.DateTimeField(auto_now_add=True)
   code_key = models.CharField(max_length=255, blank=False, null=False)
   company_name = models.CharField(max_length=255, blank=False, null=False)
   product_name = models.CharField(max_length=255, blank=False, null=False)
   batch_number = models.CharField(max_length=255, blank=False, null=False)
   user_name = models.CharField(max_length=255)
   location = models.JSONField(blank=True, null=True)
   country = models.CharField(max_length=255, blank=True, null=True)
   region = models.CharField(max_length=255, blank=True, null=True)
   city = models.CharField(max_length=255, blank=True, null=True)
   town = models.CharField(max_length=255, blank=True, null=True)
   street = models.CharField(max_length=255, blank=True, null=True)
   key_version=models.CharField(max_length=255, blank=True, null=True)
   
   class Meta:
        indexes = [
            models.Index(fields=['date_time','company_name', 'product_name', 'batch_number', 'code_key' ])
        ]
   def save(self, *args, **kwargs):
       current_key_obj = KeyManagement.get_current_key()
       if not current_key_obj:
            raise ValueError("No encryption key found in KeyManagement")
        
       current_key = current_key_obj.public_key
       current_version = current_key_obj.version
       
       if not self.key_version:
           self.code_key = EncryptionUtil.encrypt(self.code_key, current_key)
           self.company_name = EncryptionUtil.encrypt(self.company_name, current_key)
           self.product_name = EncryptionUtil.encrypt(self.product_name, current_key)
           self.batch_number = EncryptionUtil.encrypt(self.batch_number, current_key)
           self.user_name = EncryptionUtil.encrypt(self.user_name, current_key)
           self.location = EncryptionUtil.encrypt(self.location, current_key) if self.location else None
           self.country = EncryptionUtil.encrypt(self.country, current_key) if self.country else None
           self.region = EncryptionUtil.encrypt(self.region, current_key) if self.region else None
           self.city = EncryptionUtil.encrypt(self.city, current_key) if self.city else None
           self.town = EncryptionUtil.encrypt(self.town, current_key) if self.town else None
           self.street = EncryptionUtil.encrypt(self.street, current_key) if self.street else None
           self.key_version = current_version
        
       else:
           if self.key_version < current_key:
               old_key = KeyManagement.get_key_by_version(self.key_version).private_key
               self.code_key = EncryptionUtil.rotate_key(self.code_key, old_key, current_key)
               self.company_name = EncryptionUtil.rotate_key(self.company_name, old_key, current_key)
               self.product_name = EncryptionUtil.rotate_key(self.product_name, old_key, current_key)
               self.batch_number = EncryptionUtil.rotate_key(self.batch_number, old_key, current_key)
               self.user_name = EncryptionUtil.rotate_key(self.user_name, old_key, current_key)
               self.location = EncryptionUtil.rotate_key(self.location, old_key, current_key) if self.location else None
               self.country = EncryptionUtil.rotate_key(self.country, old_key, current_key) if self.country else None
               self.region = EncryptionUtil.rotate_key(self.region, old_key, current_key) if self.region else None
               self.city = EncryptionUtil.rotate_key(self.city, old_key, current_key) if self.city else None
               self.town = EncryptionUtil.rotate_key(self.town, old_key, current_key) if self.town else None
               self.street = EncryptionUtil.rotate_key(self.street, old_key, current_key) if self.street else None
               self.key_version = current_version
       
       cache_keys = [
            f"user_checkout_info_{self.user_name}",
            f"checkout_metrics_{self.company_name}"
        ]
        
        # Invalidate all related cache keys
       for key in cache_keys:
           cache_key = sanitize_cache_key(key)
           cache.delete(cache_key)

       super().save(*args, **kwargs)
  
 

@receiver(post_save, sender=ScanInfo)
@receiver(post_save, sender=CheckoutInfo)
def invalidate_shared_cache(sender, instance, **kwargs):
    cache_keys = [
        f"location_metrics_comparison_{instance.company_name}",
        f"performance_metrics_{instance.company_name}",
        f"product_user_metrics_{instance.company_name}",
        # f"line_chart_data_{instance.company_name}",
        f"product_metrics_{instance.company_name}_{instance.product_name}",
    ]
    
    # Invalidate all related cache keys
    for key in cache_keys:
        cache_key = sanitize_cache_key(key)
        cache.delete(cache_key) 


class LogProduct(models.Model):
    company_name = models.CharField(max_length=150)
    product_name = models.CharField(max_length=150)
    batch_number = models.CharField(max_length=50)
    code_key = models.CharField(max_length=300)
    perishable = models.CharField(max_length=100)
    manufacture_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    days_to_expiry = models.CharField(max_length=150, blank=True, null=True)
    message = models.CharField(max_length=255)
    FDA_number  = models.CharField(max_length=255, blank=True, null=True)
    standards_authority_number = models.CharField(max_length=255, blank=True, null=True)
    checkout_user_email = models.EmailField(max_length=200, blank=True, null=True)
    checkout_user_phone = models.PositiveBigIntegerField(blank=True, null=True)
    checkout = models.BooleanField(default=False)
    checkout_message = models.CharField(max_length=255)
    patch = models.BooleanField(default=False)
    patch_reason = models.CharField(max_length=100, blank=True, null=True)
    patch_message = models.CharField(max_length=255, blank=True, null=True)
    key_version=models.CharField(max_length=255, blank=True, null=True)
    

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
       current_key_obj = KeyManagement.get_current_key()
       if not current_key_obj:
            raise ValueError("No encryption key found in KeyManagement")
        
       current_key = current_key_obj.public_key
       current_version = current_key_obj.version
       
       if not self.key_version:
           print('key ver', self.key_version)
           self.company_name = EncryptionUtil.encrypt(self.company_name, current_key)
           self.product_name = EncryptionUtil.encrypt(self.product_name, current_key)
           self.batch_number = EncryptionUtil.encrypt(self.batch_number, current_key)
           self.code_key = EncryptionUtil.encrypt(self.code_key, current_key)
           self.perishable = EncryptionUtil.encrypt(self.perishable, current_key)
           self.manufacture_date = EncryptionUtil.encrypt(self.manufacture_date, current_key)
           self.expiry_date = EncryptionUtil.encrypt(self.expiry_date, current_key)
           self.message = EncryptionUtil.encrypt(self.message, current_key)
           self.FDA_number = EncryptionUtil.encrypt(self.FDA_number, current_key)
           self.standards_authority_number = EncryptionUtil.encrypt(self.standards_authority_number, current_key)
           self.checkout_user_email = EncryptionUtil.encrypt(self.checkout_user_email, current_key)
           self.checkout_user_phone = EncryptionUtil.encrypt(self.checkout_user_phone, current_key)
           self.checkout = EncryptionUtil.encrypt(self.checkout, current_key)
           self.checkout_message = EncryptionUtil.encrypt(self.checkout_message, current_key)
           self.patch = EncryptionUtil.encrypt(self.patch, current_key)
           self.patch_reason = EncryptionUtil.encrypt(self.patch_reason, current_key)
           self.patch_message = EncryptionUtil.encrypt(self.patch_message, current_key)
           self.key_version = current_version
        
       else:
           if self.key_version < current_key:
               print('else key ver', self.key_version)
               print('else cur ver', current_key)
               
               old_key = KeyManagement.get_key_by_version(self.key_version).private_key
               self.code_key = EncryptionUtil.rotate_key(self.code_key, old_key, current_key)
               self.company_name = EncryptionUtil.rotate_key(self.company_name, old_key, current_key)
               self.product_name = EncryptionUtil.rotate_key(self.product_name, old_key, current_key)
               self.batch_number = EncryptionUtil.rotate_key(self.batch_number, old_key, current_key)
               self.perishable = EncryptionUtil.rotate_key(self.perishable, old_key, current_key)
               self.manufacture_date = EncryptionUtil.rotate_key(self.manufacture_date, old_key, current_key)
               self.expiry_date = EncryptionUtil.rotate_key(self.expiry_date, old_key, current_key)
               self.message = EncryptionUtil.rotate_key(self.message, old_key, current_key)
               self.FDA_number = EncryptionUtil.rotate_key(self.FDA_number, old_key, current_key)
               self.standards_authority_number = EncryptionUtil.rotate_key(self.standards_authority_number, old_key, current_key)
               self.checkout_user_email = EncryptionUtil.rotate_key(self.checkout_user_email, old_key, current_key)
               self.checkout_user_phone = EncryptionUtil.rotate_key(self.checkout_user_phone, old_key, current_key)
               self.checkout = EncryptionUtil.rotate_key(self.checkout, old_key, current_key)
               self.checkout_message = EncryptionUtil.rotate_key(self.checkout_message, old_key, current_key)
               self.patch = EncryptionUtil.rotate_key(self.patch, old_key, current_key)
               self.patch_reason = EncryptionUtil.rotate_key(self.patch_reason, old_key, current_key)
               self.patch_message = EncryptionUtil.rotate_key(self.patch_message, old_key, current_key)
               self.key_version = current_version
               
       if self.pk:
            previous = LogProduct.objects.get(pk=self.pk)
            if previous.patch != self.patch or previous.checkout != self.checkout:
                cache_key = sanitize_cache_key(f"log_product_{self.company_name}_{self.product_name}_{self.batch_number}_{self.code_key}")
                cache.delete(cache_key)
                
       super().save(*args, **kwargs)
  

def sanitize_cache_key(key):
    return re.sub(r'[^A-Za-z0-9_]', '_', key)