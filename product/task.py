# tasks.py
from celery import shared_task
from .models import ScanInfo, CheckoutInfo
from .serializer import ScanInfoSerializer, CheckoutInfoSerializer
import requests
from django.core.cache import cache

@shared_task
def scan_process_location(data):
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
    
    serializer = ScanInfoSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return serializer.data
    return serializer.errors


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


