from django.db import models
from accounts.models import Company
from django.utils import timezone
import secrets


# Create your models here.
class Payment(models.Model):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="payments"
    )  # One company can have many payments

    product_name = models.CharField(max_length=120)
    batch_number = models.CharField(null=True)
    perishable = models.BooleanField(default=False)
    render_type = models.CharField(max_length=120)
    product_logo = models.ImageField(upload_to='paqs/prod_logo/', blank=True)
    manufacture_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    FDA_number  = models.CharField(max_length=255, blank=True, null=True)
    standards_authority_number = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.PositiveIntegerField(null=True)
    unit_price = models.DecimalField(null=True, max_digits=5, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    transaction_status = models.CharField(max_length=20, default='Failed')
    QRcode_status = models.CharField(max_length=20, default="Not generated")
    file_id = models.CharField(max_length=255, blank=True, null=True)
    verified = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-date_created",)

    def __str__(self):
        return f"Payment: {self.amount} for {self.company}"
    
    def get_image(self):
        if self.product_logo:
            return self.product_logo.url
        return None 
    
    def save(self, *args, **kwargs):
        # Automatically set company based on the logged-in user (if any)
        if self.company is None and self.request is not None:
            self.company = self.request.user.company
        super().save(*args, **kwargs)
