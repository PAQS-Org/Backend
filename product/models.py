from django_cassandra_engine.models import DjangoCassandraModel
from cassandra.cqlengine import columns
import re
from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver
from entry.models import KeyManagement
from PAQSBackend.encry import EncryptionUtil
# Concentrate on the generating of the codes. When you are done, then you come to this. do not over think.
class ScanInfo(DjangoCassandraModel):
   date_time = columns.DateTime().truncate_microseconds=True
   code_key = columns.Text(required=True)
   company_name = columns.Text(required=True)
   product_name = columns.Text(required=True)
   batch_number = columns.Text(required=True)
   user_name = columns.Text(max_length=255)
   location = columns.Map(columns.Text, columns.Text)
   country = columns.Text()
   region = columns.Text()
   city = columns.Text()
   town = columns.Text()
   street = columns.Text()
   key_version = columns.Integer()
   
#    class Meta:
#         indexes = [
#             columns.Index(fields=['date_time','company_name', 'product_name', 'batch_number', 'code_key' ])
#         ]
        
   def save(self, *args, **kwargs):
       current_key_obj = KeyManagement.get_current_key()
       current_key = current_key_obj.aes_key
       current_version = current_key_obj.version
       
       if not self.key_version:
           self.code_key = EncryptionUtil.encrypt(self.code_key, current_key)
           self.company_name = EncryptionUtil.encrypt(self.company_name_encrypted, current_key)
           self.product_name = EncryptionUtil.encrypt(self.product_name_encrypted, current_key)
           self.batch_number = EncryptionUtil.encrypt(self.batch_number_encrypted, current_key)
           self.user_name = EncryptionUtil.encrypt(self.user_name_encrypted, current_key)
           self.location = EncryptionUtil.encrypt(self.location_encrypted, current_key)
           self.country = EncryptionUtil.encrypt(self.country_encrypted, current_key)
           self.region = EncryptionUtil.encrypt(self.region_encrypted, current_key)
           self.city = EncryptionUtil.encrypt(self.city_encrypted, current_key)
           self.town = EncryptionUtil.encrypt(self.town_encrypted, current_key)
           self.street = EncryptionUtil.encrypt(self.street_encrypted, current_key)
           self.key_version = current_version
        
       else:
           if self.key_version < current_key:
               old_key = KeyManagement.get_key_by_version(self.key_version).aes_key
               self.code_key = EncryptionUtil.rotate_key(self.code_key, old_key, current_key)
               self.company_name = EncryptionUtil.rotate_key(self.company_name, old_key, current_key)
               self.product_name = EncryptionUtil.rotate_key(self.product_name, old_key, current_key)
               self.batch_number = EncryptionUtil.rotate_key(self.batch_number, old_key, current_key)
               self.user_name = EncryptionUtil.rotate_key(self.user_name, old_key, current_key)
               self.location = EncryptionUtil.rotate_key(self.location, old_key, current_key)
               self.country = EncryptionUtil.rotate_key(self.country, old_key, current_key)
               self.region = EncryptionUtil.rotate_key(self.region, old_key, current_key)
               self.city = EncryptionUtil.rotate_key(self.city, old_key, current_key)
               self.town = EncryptionUtil.rotate_key(self.town, old_key, current_key)
               self.street = EncryptionUtil.rotate_key(self.street, old_key, current_key)
               self.key_version = current_version
       super().save(*args, **kwargs)
  
   @property
   def code_key_encrypted(self):
        key = KeyManagement.get_key_by_version(self.key_version).aes_key
        return EncryptionUtil.decrypt(self.code_key, key)

   @property
   def company_name_encrypted(self):
        key = KeyManagement.get_key_by_version(self.key_version).aes_key
        return EncryptionUtil.decrypt(self.company_name, key)

   @property
   def product_name_encrypted(self):
        key = KeyManagement.get_key_by_version(self.key_version).aes_key
        return EncryptionUtil.decrypt(self.product_name, key)
   @property
   def batch_number_encrypted(self):
        key = KeyManagement.get_key_by_version(self.key_version).aes_key
        return EncryptionUtil.decrypt(self.batch_number, key)
   @property
   def user_name_encrypted(self):
        key = KeyManagement.get_key_by_version(self.key_version).aes_key
        return EncryptionUtil.decrypt(self.user_name, key)
   @property
   def location_encrypted(self):
        key = KeyManagement.get_key_by_version(self.key_version).aes_key
        return EncryptionUtil.decrypt(self.location, key)
   @property
   def country_encrypted(self):
        key = KeyManagement.get_key_by_version(self.key_version).aes_key
        return EncryptionUtil.decrypt(self.country, key)
   @property
   def region_encrypted(self):
        key = KeyManagement.get_key_by_version(self.key_version).aes_key
        return EncryptionUtil.decrypt(self.region, key)
   @property
   def city_encrypted(self):
        key = KeyManagement.get_key_by_version(self.key_version).aes_key
        return EncryptionUtil.decrypt(self.city, key)
   @property
   def town_encrypted(self):
        key = KeyManagement.get_key_by_version(self.key_version).aes_key
        return EncryptionUtil.decrypt(self.town, key)
   @property
   def street_encrypted(self):
        key = KeyManagement.get_key_by_version(self.key_version).aes_key
        return EncryptionUtil.decrypt(self.street, key)

class CheckoutInfo(DjangoCassandraModel):
   date_time = columns.DateTimeField(auto_now_add=True)
   code_key = columns.Text(required=True)
   company_name = columns.Text(required=True)
   product_name = columns.Text(required=True)
   batch_number = columns.Text(required=True)
   user_name = columns.Text(max_length=255)
   location = columns.JSONField()
   country = columns.Text()
   region = columns.Text()
   city = columns.Text()
   town = columns.Text()
   street = columns.Text()
   
   class Meta:
        indexes = [
            columns.Index(fields=['date_time','company_name', 'product_name', 'batch_number', 'code_key' ])
        ]
   
   def save(self, *args, **kwargs):
        # List of cache keys you want to invalidate
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


class LogProduct(DjangoCassandraModel):
    company_name = columns.Text(max_length=100)
    product_name = columns.Text(max_length=100)
    batch_number = columns.Text(max_length=50)
    code_key = columns.Text(max_length=300)
    perishable = columns.Text(max_length=100)
    manufacture_date = columns.DateField(blank=True, null=True)
    expiry_date = columns.DateField(blank=True, null=True)
    message = columns.Text(max_length=255)
    checkout_user_email = columns.EmailField(max_length=200, blank=True, null=True)
    checkout_user_phone = columns.PositiveBigIntegerField(blank=True, null=True)
    checkout = columns.BooleanField(default=False)
    checkout_message = columns.Text(max_length=255)
    patch = columns.BooleanField(default=False)
    patch_reason = columns.Text(max_length=100, blank=True, null=True)
    patch_message = columns.Text(max_length=255)

    class Meta:
        db_table = 'LogProduct'
        managed = True
        verbose_name = 'Logproduct'
        verbose_name_plural = 'Logproducts'
        indexes = [
            columns.Index(fields=['code_key', 'company_name', 'product_name', 'batch_number'])
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