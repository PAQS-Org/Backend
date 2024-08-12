from rest_framework import serializers
from .models import Payment
from accounts.models import Company
from .prices import calculate_unit_price


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
    

    # def create(self, validated_data):
    #     request = self.context.get('request')
    #     quantity = validated_data.get('quantity')
    #     product_name = validated_data.get('product_name')
    #     batch_number = validated_data.get('batch_number')
    #     perishable = validated_data.get('perishable')
    #     manufacture_date = validated_data.get('manufacture_date')
    #     expiry_date = validated_data.get('expiry_date')
    #     render_type = validated_data.get('render_type')
    #     quantity = validated_data.get('quantity')
    #     amount, _, unit_price = calculate_unit_price(quantity)
        
    #     # Create the Payment instance
    #     payment = Payment.objects.create(
    #         company=Company.objects.get(email=request.user),
    #         quantity=quantity,
    #         amount=amount,
    #         unit_price=unit_price,
    #         perishable=perishable,
    #         render_type=render_type,
    #         manufacture_date=manufacture_date,
    #         expiry_date=expiry_date,
    #         product_name=product_name,
    #         batch_number=batch_number,
    #         product_logo=validated_data.get('product_logo'), 
    #         **validated_data,
    #     )
    #     return payment
