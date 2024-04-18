from django.db import models
from accounts.models import Company, User
import string
import random
# Create your models here.



def generate_batch_code(product_name):
  # Generate a random alphanumeric code (length 3)
  random_code = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(3))
  return product_name[:3].upper() + random_code


def generate_unique_id(batch_code):
  # Generate a random alphanumeric code (length 6)
  random_code = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
  return batch_code + random_code

class ProductsInfo(models.Model):
    company_name = models.ForeignKey(to=Company, on_delete=models.CASCADE, related_name="companyInfo")
    batch_number = models.CharField(max_length=7)
    product_name = models.CharField(max_length=50)
    perishable = models.BooleanField(default=False)
    manufacture_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    render_type = models.CharField(max_length=7)
    checkout = models.BooleanField(default=False)
    reference_id = models.CharField(max_length=7, unique=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.batch_number:
        # Generate batch code only on first save
            self.batch_number = generate_batch_code(self.product_name)
        if not self.reference_id:
        # Generate unique ID for each item
            self.reference_id = generate_unique_id(self.batch_number)
        super().save(*args, **kwargs)

# Concentrate on the generating of the codes. When you are done, then you come to this. do not over think.
# class ScanInfo(models.Model):
#    product_name = models.ForeignKey(to=ProductsInfo)
#    user_name = models.ForeignKey(to=User, on_delete=models.CASCADE)
