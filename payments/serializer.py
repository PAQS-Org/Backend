from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = ['id','transaction_id','product_name', 'batch_number', 'date_created','unit_price' ,'quantity', 'amount', ]
