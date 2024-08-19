from rest_framework import serializers
from .models import Payment
from accounts.models import Company
from .prices import calculate_unit_price


class PaymentSerializer(serializers.ModelSerializer):
    amount = serializers.CharField(read_only=True)
    company = serializers.CharField(read_only=True)
    class Meta:
        model = Payment
        fields = '__all__'
    
    def create(self, validated_data):
        request = self.context.get('request')
        quantity = validated_data.get('quantity')
        amount, _, unit_price = calculate_unit_price(quantity)
        
        # Create the Payment instance
        payment = Payment.objects.create(
            company=Company.objects.get(email=request.user),
            amount=amount,
            unit_price=unit_price,
            **validated_data,
        )
        return payment
    