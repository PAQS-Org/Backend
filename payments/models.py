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
    batch_number = models.CharField(max_length=120,null=True)
    quantity = models.PositiveIntegerField(null=True)
    unit_price = models.DecimalField(null=True, max_digits=5, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    transaction_status = models.CharField(max_length=20)
    verified = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-date_created",)

    def __str__(self):
        return f"Payment: {self.amount} for {self.product_name}"

    def save(self, *args, **kwargs):
        # Automatically set company based on the logged-in user (if any)
        if self.company is None and self.request is not None:
            self.company = self.request.user.company
        super().save(*args, **kwargs)
