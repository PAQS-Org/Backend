import re
from celery import shared_task
from .models import ScanInfo, LogProduct
from .serializer import CheckoutInfoSerializer, ScanInfoSerializer
import requests
from django.core.cache import cache


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
    print('geo_serializer', updated_serializer)
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
        return {'error': 'Product not found'}

    result = {
                'message': log_product.patch_message if log_product.patch else log_product.checkout_message if log_product.checkout else log_product.message,
                'company_name': log_product.company_name,
                'product_name': log_product.product_name
              }
    cache.set(cache_key, result, timeout=86400)
    return result



@shared_task
def checkout_process_location(data):
    location = data.get('location')
    
    # Check cache for geocoding results
    geocode_data = cache.get(location)
    if not geocode_data:
        # Use a geocoding service to decode the location
        geocode_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={location.split(',')[0]}&lon={location.split(',')[1]}"
        response = requests.get(geocode_url)
        if response.status_code != 200:
            return {'error': 'Could not decode location'}
        
        geocode_data = response.json()
        # Cache the geocoding result
        cache.set(location, geocode_data, timeout=86400)  # Cache for 24 hours
    
    address = geocode_data.get('address', {})
    
    country = address.get('country', '')
    region = address.get('state', '')
    city = address.get('city', '') or address.get('town', '') or address.get('village', '')
    town = address.get('town', '') or address.get('village', '')
    street = address.get('road', '')
    
    # Update data with decoded location fields
    data.update({
        'country': country,
        'region': region,
        'city': city,
        'town': town,
        'street': street,
        'raw_location': location
    })
    
    serializer = CheckoutInfoSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return serializer.data
    return serializer.errors


