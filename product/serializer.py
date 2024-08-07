from rest_framework import serializers
from .models import ProductsInfo, ScanInfo, CheckoutInfo

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
