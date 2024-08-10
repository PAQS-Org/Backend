from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    amount = serializers.CharField(read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id',
            'transaction_id',
            'product_name', 
            'batch_number',
            'product_logo',
            'render_type',
            'perishable', 
            'manufacture_date', 
            'expiry_date',
            'date_created', 
            'unit_price',
            'quantity', 
            'amount', 
            ]
