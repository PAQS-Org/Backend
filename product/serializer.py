from rest_framework import serializers
from .models import ProductsInfo, ScanInfo, CheckoutInfo, LogProduct
from accounts.models import Company, User
from .task import scan_process_location


class ProductInfoSerializer(serializers.ModelSerializer):
  class Meta:
    model = ProductsInfo
    fields = '__all__'



class ScanInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanInfo
        fields = '__all__'

    def create(self, validated_data):
        request = self.context.get('request')
        location = validated_data.get('location')

        # Asynchronous processing of the location data
        from .task import scan_process_location
        scan_process_location.delay(location, validated_data)

        return super().create(validated_data)


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