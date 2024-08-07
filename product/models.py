from django.db import models
from accounts.models import Company, User
import string
import random

# def generate_unique_id(batch_code):
#   # Generate a random alphanumeric code (length 6)
#   random_code = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
#   return batch_code + random_code

class ProductsInfo(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    company_name = models.ForeignKey(to=Company, on_delete=models.CASCADE, related_name="companyInfo")
    batch_number = models.CharField(max_length=7)
    product_name = models.CharField(max_length=50)
    perishable = models.BooleanField(default=False)
    manufacture_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    render_type = models.CharField(max_length=7)
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
   code_key = models.CharField(max_length=255, blank=False, null=False)
   company_name = models.ForeignKey(to=Company, on_delete=models.CASCADE, related_name="companyInfo")
   product_name = models.ForeignKey(to=ProductsInfo)
   user_name = models.ForeignKey(to=User, on_delete=models.CASCADE)
   location = models.CharField(max_length=255)
   country = models.CharField(max_length=255)
   region = models.CharField(max_length=255)
   city = models.CharField(max_length=255)
   town = models.CharField(max_length=255, blank=True, null=True)
   street = models.CharField(max_length=255, blank=True, null=True)


class CheckoutInfo(models.Model):
   code_key = models.CharField(max_length=255, blank=False, null=False)
   company_name = models.ForeignKey(to=Company, on_delete=models.CASCADE, related_name="companyInfo")
   product_name = models.ForeignKey(to=ProductsInfo)
   user_name = models.ForeignKey(to=User, on_delete=models.CASCADE)
   location = models.CharField(max_length=255)
   country = models.CharField(max_length=255)
   region = models.CharField(max_length=255)
   city = models.CharField(max_length=255)
   town = models.CharField(max_length=255, blank=True, null=True)
   street = models.CharField(max_length=255, blank=True, null=True)

