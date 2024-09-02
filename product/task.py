import re
from celery import shared_task
from .models import ScanInfo, LogProduct
from accounts.models import Company
from payments.models import Payment
from .serializer import CheckoutInfoSerializer, ScanInfoSerializer
import requests
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from django.conf import settings
import boto3



def sanitize_cache_key(key):
    return re.sub(r'[^A-Za-z0-9_]', '_', key)

def scan_process_location(location, serializer):
    # Geocoding location
    cache_key = sanitize_cache_key(f"geocode_{location['latitude']},{location['longitude']}")
    geocode_data = cache.get(cache_key)

    print('geo cache key', cache_key)
    print('geocode_data', geocode_data)

    headers = {'User-Agent': 'backendPAQS/1.0 (bra.kwameadu3@gmail.com)'}
    if not geocode_data:
        geocode_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={location['latitude']}&lon={location['longitude']}"
        response = requests.get(geocode_url, headers=headers)
        print('geo_response', response)
        if response.status_code != 200:
            return {'error': 'Could not decode location'}

        geocode_data = response.json()
        cache.set(cache_key, geocode_data, timeout=86400)

    address = geocode_data.get('address', {})
    
    decoded_data = {
        'country': address.get('country', ''),
        'region': address.get('state', ''),
        'city': address.get('city', '') or address.get('town', '') or address.get('village', ''),
        'town': address.get('town', '') or address.get('village', ''),
        'street': address.get('road', ''),
        'raw_location': location
    }
    print('decoded message', decoded_data)

    # Merge decoded data with existing validated data
    validated_data = serializer.validated_data.copy()
    validated_data.update(decoded_data)

    # Save the updated data
    updated_serializer = ScanInfoSerializer(data=validated_data)
    if updated_serializer.is_valid():
        updated_serializer.save()
    else:
        print('Validation errors:', updated_serializer.errors)



def hierarchical_search(company_name, product_name, batch_number, code_key):
    cache_key = sanitize_cache_key(f"log_product_{company_name}_{product_name}_{batch_number}_{code_key}")
    cached_result = cache.get(cache_key)

    if cached_result:
        return cached_result
    try:
        log_product = LogProduct.objects.get(
            company_name=company_name,
            product_name=product_name,
            batch_number=batch_number,
            code_key=code_key
        )
    except LogProduct.DoesNotExist:
        return {'error': 'Product not found', 'status': status.HTTP_404_NOT_FOUND}

    try:
        company = Company.objects.get(company_name=company_name)
        
        payment = Payment.objects.filter(
            company=company,
            product_name=product_name,
            batch_number=batch_number
        ).first()
        product_logo_url = payment.get_image() if payment else None
        product_logo = get_presigned_url(product_logo_url)
    
    except Payment.DoesNotExist:
        product_logo_url = None

    if log_product.patch:
        message = log_product.patch_message
        product_logo_url = product_logo
        status_code = status.HTTP_202_ACCEPTED
    elif log_product.checkout:
        message = log_product.checkout_message
        status_code = status.HTTP_404_NOT_FOUND
    else:
        message = log_product.message
        status_code = status.HTTP_200_OK

    result = {
        'message': message,
        'company_name': log_product.company_name,
        'product_name': log_product.product_name,
        'batch_number': log_product.batch_number,
        'patch': log_product.patch,
        'product_logo_url': product_logo,  # Include the product logo URL
        'status': status_code
    }

    # Cache the result if needed
    cache.set(cache_key, result, timeout=3600)

    return result

def get_presigned_url(s3_key):
    # file_key = f"static/{s3_key}"
    s3 = boto3.client('s3', 
                      aws_access_key_id=settings.AWS_ACCESS_KEY_ID, 
                      aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, 
                      region_name=settings.AWS_S3_REGION_NAME)
    presigned_url = s3.generate_presigned_url('get_object',
                                              Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                                      'Key': s3_key},
                                              ExpiresIn=3600)  # URL valid for 1 hour
    return presigned_url

@shared_task
def checkout_process_location(location, serializer):
 # Geocoding location
    cache_key = sanitize_cache_key(f"geocode_{location['latitude']},{location['longitude']}")
    geocode_data = cache.get(cache_key)

    print('geo cache key', cache_key)
    print('geocode_data', geocode_data)

    headers = {'User-Agent': 'backendPAQS/1.0 (bra.kwameadu3@gmail.com)'}
    if not geocode_data:
        geocode_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={location['latitude']}&lon={location['longitude']}"
        response = requests.get(geocode_url, headers=headers)
        print('geo_response', response)
        if response.status_code != 200:
            return {'error': 'Could not decode location'}

        geocode_data = response.json()
        cache.set(cache_key, geocode_data, timeout=86400)

    address = geocode_data.get('address', {})
    
    decoded_data = {
        'country': address.get('country', ''),
        'region': address.get('state', ''),
        'city': address.get('city', '') or address.get('town', '') or address.get('village', ''),
        'town': address.get('town', '') or address.get('village', ''),
        'street': address.get('road', ''),
        'raw_location': location
    }
    print('decoded message', decoded_data)

    # Merge decoded data with existing validated data
    validated_data = serializer.validated_data.copy()
    validated_data.update(decoded_data)

    # Save the updated data
    updated_serializer = CheckoutInfoSerializer(data=validated_data)
    if updated_serializer.is_valid():
        updated_serializer.save()
    else:
        print('Validation errors:', updated_serializer.errors)


