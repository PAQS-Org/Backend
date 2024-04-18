from rest_framework import serializers
from .models import ProductsInfo

class ProductInfoSerializer(serializers.ModelSerializer):
  class Meta:
    model = ProductsInfo
    fields = '__all__'
