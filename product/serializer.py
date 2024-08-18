from rest_framework import serializers
from .models import ProductsInfo, ScanInfo, CheckoutInfo, LogProduct



class ProductInfoSerializer(serializers.ModelSerializer):
  class Meta:
    model = ProductsInfo
    fields = '__all__'



class ScanInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanInfo
        fields = '__all__'


class CheckoutInfoSerializer(serializers.ModelSerializer):
  class Meta:
    model = CheckoutInfo
    fields = '__all__'


class LogProductSerializer(serializers.ModelSerializer):
  class Meta:
    model = LogProduct
    fields = '__all__'

  def create(self, validated_data):
    return super().create(validated_data)