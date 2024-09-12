from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from PAQSBackend.encry import (
    generate_rsa_key_pair, serialize_public_key, deserialize_public_key,
    decrypt_session_key, encrypt_data, serialize_private_key
)
from base64 import urlsafe_b64encode, urlsafe_b64decode

from .models import LogProduct, ScanInfo, CheckoutInfo
from django.db.models import Count, F,Q
from django.db.models.functions import TruncYear, TruncMonth, TruncDay, TruncHour
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsOwner, IsUser
from .serializer import CheckoutInfoSerializer, ScanInfoSerializer, LogProductSerializer
from .task import scan_process_location, checkout_process_location, hierarchical_search
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
import logging
from smtplib import SMTPException
from django.utils import timezone
import datetime
import calendar
import re

def sanitize_cache_key(key):
    return re.sub(r'[^A-Za-z0-9_]', '_', key)

class ScanInfoView(APIView):
    permission_classes = (IsAuthenticated, IsUser, IsOwner)
    serializer_class = ScanInfoSerializer

    def post(self, request):
        qr_code = request.data.get('qr_code')
        email = request.data.get('email')
        location = request.data.get('location')  

        if not qr_code or '/' not in qr_code or qr_code.startswith('http://'):
            return Response({'message': f'{qr_code} is not the expected data'}, status=status.HTTP_404_NOT_FOUND)

        try:
            x, y, z, code_key, company_name, product_name, batch = qr_code.split('/')
            batch_number = batch[:-1]
        except ValueError:
            return Response({'message': f'{qr_code} is an invalid format'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            search_result = hierarchical_search(company_name, product_name, batch_number, code_key)

            # Extract message and status code
            message = search_result.get('message')
            company_name = search_result.get('company_name')
            product_name = search_result.get('product_name')
            batch_number = search_result.get('batch_number')
            product_logo = search_result.get('product_logo_url')
            patch = search_result.get('patch')
            status_code = search_result.get('status')

            if ScanInfo.objects.filter(
                code_key__iexact=code_key,
                company_name__iexact=company_name,
                product_name__iexact=product_name,
                batch_number__iexact=batch_number,
                user_name__iexact=email
            ).exists():
                return Response({
                    'message': message, 
                    'company_name': company_name,
                    'product_name': product_name,
                    'batch_number': batch_number,
                    'product_logo': product_logo, 
                    'patch': patch, 
                    }, status=status_code)

            # Store the scan information in the database
            scan_data = {
                'code_key': code_key,
                'company_name': company_name,
                'product_name': product_name,
                'batch_number': batch_number,
                'user_name': email,
                'location': location,
            }
            serializer = self.serializer_class(data=scan_data, context={'request': request})
            if serializer.is_valid():
                scan_info = serializer.save()

                # Process location asynchronously if provided
                if location:
                    scan_process_location(scan_info.location, serializer)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Return the message after storing the scan information
            return Response({
                    'message': message, 
                    'company_name': company_name,
                    'product_name': product_name,
                    'batch_number': batch_number,
                    'product_logo': product_logo, 
                    'patch': patch, 
                    }, status=status_code)

        except LogProduct.DoesNotExist:
            return Response({'message': 'Last part of the code not found'}, status=status.HTTP_404_NOT_FOUND)

class CheckoutInfoView(APIView):
    permission_classes = (IsAuthenticated, IsUser, IsOwner)
    serializer_class = CheckoutInfoSerializer  

    def post(self, request):
        qr_code = request.data.get('qr_code')
        email = request.data.get('email')
        location = request.data.get('location') 
        
        try:
            # Extract QR code information
            x, y, z, code_key, company_name, product_name, batch = qr_code.split('/')
            batch_number = batch[:-1]

            # Find the item in LogProduct table
            try:
                log_product = LogProduct.objects.get(
                    code_key=code_key,
                    company_name=company_name,
                    product_name=product_name,
                    batch_number=batch_number
                )

                # Update checkout status and message
                log_product.checkout_user_email = email
                log_product.checkout = True
                log_product.checkout_message = f"{product_name} from {company_name} has been purchased"
                log_product.save()

                # Store the checkout information in the CheckoutInfo table
                checkout_data = {
                    'code_key': code_key,
                    'company_name': company_name,
                    'product_name': product_name,
                    'batch_number': batch_number,
                    'user_name': email,
                    'location': location,
                }
                serializer = self.serializer_class(data=checkout_data, context={'request': request})
                if serializer.is_valid():
                    checkout_info = serializer.save()
                    
           
                    if location:
                        checkout_process_location(checkout_info.location, serializer)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                # Return the checkout message
                return Response({'message': log_product.checkout_message}, status=status.HTTP_200_OK)

            except LogProduct.DoesNotExist:
                return Response({'message': 'Product does not exist'}, status=status.HTTP_404_NOT_FOUND)

        except ValueError:
            return Response({'message': 'Invalid QR code format'}, status=status.HTTP_400_BAD_REQUEST)

class PatchInfoView(APIView):
    permission_classes = (IsAuthenticated, IsOwner)
    serializer_class = LogProductSerializer

    def post(self, request):
        comp_name = request.data.get('company_name')
        prod_name = request.data.get('product_name')
        batch_number = request.data.get('batch_number')
        patch_reason = request.data.get('patch_reason')
        patch_message = request.data.get('patch_message')

        # Validate that all required fields are provided
        if not all([comp_name, prod_name, batch_number, patch_reason, patch_message]):
            return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Filter LogProduct objects based on the given company_name, product_name, and batch_number
        log_products = LogProduct.objects.filter(
            company_name=comp_name,
            product_name=prod_name,
            batch_number=batch_number
        )

        if log_products.exists():
            # Update the patch-related fields for all matching LogProduct objects
            log_products.update(
                patch=True,
                patch_reason=patch_reason,
                patch_message=patch_message
            )

            for log_product in log_products:
                if log_product.checkout and log_product.checkout_user_email:
                    user_email = log_product.checkout_user_email
                    self.send_checkout_email(user_email, log_product)
            return Response({"message": "Patch information updated successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "No matching product found."}, status=status.HTTP_404_NOT_FOUND)

    
    
    def send_checkout_email(self, user_email, log_product):
        subject = f"Product Information Update: {log_product.product_name} of {log_product.batch_number}"
        message = (
            f"Hello,\n\n"
            f"{log_product.company_name} has updated the information for {log_product.product_name} "
            f"of batch number {log_product.batch_number} with the following message:\n\n"
            f"\"{log_product.patch_message}\"\n\n"
            f"Please take note of the message and its necessary instructions.\n\n"
            f"Best regards,\n"
            f"PAQS Team"
        )
        from_email = settings.DEFAULT_FROM_EMAIL  # Ensure you have this set in your settings.py

        try:
            # Attempt to send the email
            send_mail(subject, message, from_email, [user_email])
            logging.info(f"Email sent successfully to {user_email}")
        except BadHeaderError:
            logging.error(f"Invalid header found when sending email to {user_email}")
        except SMTPException as e:
            logging.error(f"SMTP error occurred when sending email to {user_email}: {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error occurred when sending email to {user_email}: {str(e)}")

class ScanMetricsView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]
    
    @method_decorator(cache_page(60 * 1))
    def get(self, request, *args, **kwargs):
        company_name = request.query_params.get('company_name')
        if company_name:

            cache_key = sanitize_cache_key(f"scan_metrics_{company_name}")
            data = cache.get(cache_key)

            if not data:
                # Filter out rows with any null values
                filtered_data = ScanInfo.objects.filter(
                    company_name__iexact=company_name
                ).exclude(
                    Q(country__isnull=True) | Q(country='') |
                    Q(region__isnull=True) | Q(region='') |
                    Q(city__isnull=True) | Q(city='') 
                )

                # Total rows with no null values
                total_rows = filtered_data.count()

                # Current month filter
                current_month = timezone.now().month
                rows_current_month = filtered_data.filter(
                    date_time__month=current_month
                ).count()

                # Growth rate per previous day
                yesterday = timezone.now().date() - datetime.timedelta(days=1)
                day_before_yesterday = timezone.now().date() - datetime.timedelta(days=2)
                rows_yesterday = filtered_data.filter(
                    date_time=yesterday
                ).count()
                rows_day_before_yesterday = filtered_data.filter(
                    date_time=day_before_yesterday
                ).count()
                growth_rate_previous_day = (
                    (rows_yesterday - rows_day_before_yesterday) / rows_day_before_yesterday
                ) * 100 if rows_day_before_yesterday > 0 else 0

                # Annual growth rate
                current_year = timezone.now().year
                rows_current_year = filtered_data.filter(
                    date_time__year=current_year
                ).count()
                rows_last_year = filtered_data.filter(
                    date_time__year=current_year - 1
                ).count()
                annual_growth_rate = (
                    (rows_current_year - rows_last_year) / rows_last_year
                ) * 100 if rows_last_year > 0 else 0

                data = {
                    "scan_total_rows": total_rows,
                    "scan_current_month_name": calendar.month_name[datetime.date.today().month],
                    "scan_rows_current_month": rows_current_month,
                    "scan_growth_rate_previous_day": growth_rate_previous_day,
                    "scan_annual_growth_rate": annual_growth_rate
                }
                cache.set(cache_key, data, timeout=60 * 60)

            return Response(data)
        return Response({'message': "Company doesn't exist"}, status=status.HTTP_404_NOT_FOUND)
    
class CheckoutMetricsView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]
    @method_decorator(cache_page(60 * 1))
    def get(self, request, *args, **kwargs):
        company_name = request.query_params.get('company_name')
        if company_name:

            cache_key = sanitize_cache_key(f"checkout_metrics_{company_name}")
            data = cache.get(cache_key)

            if not data:
                # Filter out rows with any null values
                filtered_data = CheckoutInfo.objects.filter(
                    company_name__iexact=company_name
                ).exclude(
                    Q(country__isnull=True) | Q(country='') |
                    Q(region__isnull=True) | Q(region='') |
                    Q(city__isnull=True) | Q(city='') 
                )

                # Total rows with no null values
                total_rows = filtered_data.count()

                # Current month filter
                current_month = timezone.now().month
                rows_current_month = filtered_data.filter(date_time__month=current_month).count()

                # Growth rate per previous day
                yesterday = timezone.now().date() - datetime.timedelta(days=1)
                day_before_yesterday = timezone.now().date() - datetime.timedelta(days=2)
                rows_yesterday = filtered_data.filter(date_time=yesterday).count()
                rows_day_before_yesterday = filtered_data.filter(
                    date_time=day_before_yesterday
                ).count()
                growth_rate_previous_day = (
                    (rows_yesterday - rows_day_before_yesterday) / rows_day_before_yesterday
                ) * 100 if rows_day_before_yesterday > 0 else 0
                # Annual growth rate
                current_year = timezone.now().year
                rows_current_year = filtered_data.filter(
                    date_time__year=current_year
                ).count()
                rows_last_year = filtered_data.filter(
                    date_time__year=current_year - 1
                ).count()
                annual_growth_rate = (
                    (rows_current_year - rows_last_year) / rows_last_year
                ) * 100 if rows_last_year > 0 else 0

                data = {
                    "total_rows": total_rows,
                    "current_month_name": calendar.month_name[datetime.date.today().month],
                    "rows_current_month": rows_current_month,
                    "growth_rate_previous_day": growth_rate_previous_day,
                    "annual_growth_rate": annual_growth_rate
                }
                

                cache.set(cache_key, data, timeout=60 * 60)

            return Response(data)
        return Response({'message': "Company doesn't exist"}, status=status.HTTP_404_NOT_FOUND)
    
class TopLocationMetrics(APIView):
    permission_classes = [IsAuthenticated]
    
    @method_decorator(cache_page(60 * 5))
    def get(self, request, *args, **kwargs):
        company_name = request.query_params.get('company_name')
        if company_name:
            cache_key = sanitize_cache_key(f"location_metrics_comparison_{company_name}")
            data = cache.get(cache_key)

            if not data:
                location_fields = ['country', 'region', 'city', 'town']

                # CheckoutInfo Metrics
                checkout_queryset = CheckoutInfo.objects.filter(company_name=company_name).exclude(
                    Q(country='') | Q(country__isnull=True) |
                    Q(region='') | Q(region__isnull=True) |
                    Q(city='') | Q(city__isnull=True) |
                    Q(town='') | Q(town__isnull=True)
                )

                # Get distinct location with highest count
                highest_checkout_location = checkout_queryset.values(*location_fields).annotate(count=Count('id')).order_by('-count').first()

                # Get product_name with the highest count for that location
                highest_checkout_product = checkout_queryset.filter(
                    **{field: highest_checkout_location[field] for field in location_fields}
                ).values('product_name').annotate(total=Count('id')).order_by('-total').first()

                # Get the count value of the same distinct location from ScanInfo
                scan_queryset = ScanInfo.objects.filter(company_name__iexact=company_name).exclude(
                    Q(country='') | Q(country__isnull=True) |
                    Q(region='') | Q(region__isnull=True) |
                    Q(city='') | Q(city__isnull=True) |
                    Q(town='') | Q(town__isnull=True)
                )
                matching_scan_location_count = scan_queryset.filter(
                    **{field: highest_checkout_location[field] for field in location_fields}
                ).count()

                # Current Month Metrics
                current_month = timezone.now().month
                current_month_checkout_queryset = checkout_queryset.filter(date_time__month=current_month)
                current_month_scan_queryset = scan_queryset.filter(date_time__month=current_month)

                # Distinct location with highest count for current month
                highest_checkout_location_month = current_month_checkout_queryset.values(*location_fields).annotate(count=Count('id')).order_by('-count').first()

                # Product_name with the highest count for that location in the current month
                highest_checkout_product_month = current_month_checkout_queryset.filter(
                    **{field: highest_checkout_location_month[field] for field in location_fields}
                ).values('product_name').annotate(total=Count('id')).order_by('-total').first()
                
                highest_scan_product_month = current_month_scan_queryset.filter(
                    **{field: highest_checkout_location_month[field] for field in location_fields}
                ).values('product_name').annotate(total=Count('id')).order_by('-total').first()

                # Get the count value of the same distinct location from ScanInfo for the current month
                matching_scan_location_count_month = scan_queryset.filter(
                    **{field: highest_checkout_location_month[field] for field in location_fields},
                    date_time__month=current_month
                ).count()
                conversion = (highest_checkout_product_month['total'] / highest_scan_product_month['total']) * 100 if highest_scan_product_month['total'] != 0 else 0


                data = {
                    "highest_checkout_location": highest_checkout_location,
                    "highest_checkout_product": highest_checkout_product,
                    "matching_scan_location_count": matching_scan_location_count,
                    "highest_checkout_location_month": {
                        "location": highest_checkout_location_month,
                        "value": highest_checkout_location_month['count'],
                        "product_name": highest_checkout_product_month['product_name'],
                        "product_value": highest_checkout_product_month['total'],
                        "month": timezone.now().strftime("%B")
                    },
                    "matching_scan_location_count_month": matching_scan_location_count_month,
                    "highest_scan_product_month": highest_scan_product_month,
                    "conversion_rate":conversion
                }

                cache.set(cache_key, data, timeout=60 * 60)  # Cache for 1 hour

            return Response(data)
        return Response({'message': "Company doesn't exist"}, status=status.HTTP_404_NOT_FOUND)

class PerformanceMetricsView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]
        
    @method_decorator(cache_page(60 * 1))    
    def get(self, request, *args, **kwargs):
        company_name = request.query_params.get('company_name')  # Assuming the user model has a company_name field
        cache_key = sanitize_cache_key(f"performance_metrics_{company_name}")
        data = cache.get(cache_key)

        if not data:
            # 1. Conversion rate calculation (only considering rows with no null values)
            scan_queryset = ScanInfo.objects.filter(
                company_name__iexact=company_name
            ).exclude(
                Q(country='') | Q(country__isnull=True) |
                Q(region='') | Q(region__isnull=True) |
                Q(city='') | Q(city__isnull=True) |
                Q(town='') | Q(town__isnull=True)
            )
            checkout_queryset = CheckoutInfo.objects.filter(
                company_name__iexact=company_name
            ).exclude(
                Q(country='') | Q(country__isnull=True) |
                Q(region='') | Q(region__isnull=True) |
                Q(city='') | Q(city__isnull=True) |
                Q(town='') | Q(town__isnull=True)
            )

            total_scans = scan_queryset.count()
            total_checkouts = checkout_queryset.count()
            conversion_rate = (total_checkouts / total_scans) * 100 if total_scans > 0 else 0

            # 2. Month and year with the highest checkout
            checkout_by_month = checkout_queryset.annotate(
                year=F('date_time__year'),
                month=F('date_time__month')
            ).values('year', 'month').annotate(
                checkout_count=Count('id')
            ).order_by('-checkout_count').first()

            if checkout_by_month:
                highest_checkout_month = f"{timezone.datetime(1900, checkout_by_month['month'], 1).strftime('%B')}, {checkout_by_month['year']}"
                highest_checkout_month_value = checkout_by_month['checkout_count']
            else:
                highest_checkout_month = None
                highest_checkout_month_value = 0

            # 3. Product name with the highest checkout count
            highest_checkout_product = checkout_queryset.values('product_name').annotate(
                product_count=Count('id')
            ).order_by('-product_count').first()

            highest_checkout_product_name = highest_checkout_product['product_name'] if highest_checkout_product else None
            highest_checkout_product_value = highest_checkout_product['product_count'] if highest_checkout_product else 0

            data = {
                "conversion_rate": conversion_rate,
                "highest_checkout_month": highest_checkout_month,
                "highest_checkout_month_value": highest_checkout_month_value,
                "highest_checkout_product_name": highest_checkout_product_name,
                "highest_checkout_product_value": highest_checkout_product_value,
            }

            # Cache the results
            cache.set(cache_key, data, timeout=60 * 60)  # Cache for 1 hour

        return Response(data)
    
class ProductAndUserMetricsView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request, *args, **kwargs):
        company_name = request.query_params.get('company_name')
        cache_key = sanitize_cache_key(f"product_user_metrics_{company_name}")
        data = cache.get(cache_key)

        if not data:
            scan_queryset = ScanInfo.objects.filter(
                company_name__iexact=company_name
            ).exclude(
                Q(country='') | Q(country__isnull=True) |
                Q(region='') | Q(region__isnull=True) |
                Q(city='') | Q(city__isnull=True) |
                Q(town='') | Q(town__isnull=True)
            )
            checkout_queryset = CheckoutInfo.objects.filter(
                company_name__iexact=company_name
            ).exclude(
                Q(country='') | Q(country__isnull=True) |
                Q(region='') | Q(region__isnull=True) |
                Q(city='') | Q(city__isnull=True) |
                Q(town='') | Q(town__isnull=True)
            )

            checkout_products = checkout_queryset.values('product_name').annotate(checkout_count=Count('id'))

            scan_products = scan_queryset.values('product_name').annotate(scan_count=Count('id'))

            # Query distinct user names and their counts from CheckoutInfo
            checkout_users = checkout_queryset.values('user_name').annotate(checkout_count=Count('id'))

            # Query distinct user names and their counts from ScanInfo
            scan_users = scan_queryset.values('user_name').annotate(scan_count=Count('id'))

            # Getting the product_name with the highest count per user in CheckoutInfo
            user_product_counts = []
            for user in checkout_users:
                highest_product = checkout_queryset.filter(
                    user_name=user['user_name']
                ).values('product_name').annotate(total=Count('id')).order_by('-total').first()
                
                user_product_counts.append({
                    "user_name": user['user_name'],
                    "checkout_count": user['checkout_count'],
                    "product_name": highest_product['product_name'],
                    "count": highest_product['total']
                })

            # Ordering the results in ascending order based on the checkout count
            checkout_products = sorted(checkout_products, key=lambda x: x['checkout_count'])
            scan_products = sorted(scan_products, key=lambda x: x['scan_count'])
            checkout_users = sorted(checkout_users, key=lambda x: x['checkout_count'])
            scan_users = sorted(scan_users, key=lambda x: x['scan_count'])
            user_product_counts = sorted(user_product_counts, key=lambda x: x['checkout_count'])

            data = {
                "checkout_products": checkout_products,
                "scan_products": scan_products,
                "checkout_users": checkout_users,
                "scan_users": scan_users,
                "user_product_counts": user_product_counts
            }

            # Cache the results
            cache.set(cache_key, data, timeout=60 * 60)  # Cache for 1 hour

        return Response(data)

class LineChartDataView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]
    
    def get(self, request, *args, **kwargs):
        company_name = request.query_params.get('company_name')
        selected_year = request.query_params.get('year')
        selected_month = request.query_params.get('month')
        selected_day = request.query_params.get('day')
        
        # Ensure company name is provided
        if company_name:   
       
            cache_key = sanitize_cache_key(f"line_chart_data_{company_name}_{selected_year}_{selected_month}_{selected_day}")
            data = cache.get(cache_key)
            
            if not data:
                
                       
            # Convert parameters to integers if they are provided
                selected_year = int(selected_year) if selected_year else None
                selected_month = int(selected_month) + 1 if selected_month else None  # JS month is 0-indexed
                selected_day = int(selected_day) if selected_day else None

                # Build the query filters
                filters = Q(company_name=company_name)
                
                # Exclude rows with null values in any of the relevant location columns
                filters &= Q(country__isnull=False) & Q(region__isnull=False) & Q(city__isnull=False) \
                        & Q(town__isnull=False) & Q(street__isnull=False)
                
                # Apply year, month, day filters
                if selected_year:
                    filters &= Q(date_time__year=selected_year)
                if selected_month:
                    filters &= Q(date_time__month=selected_month)
                if selected_day:
                    filters &= Q(date_time__day=selected_day)

                # Determine the aggregation level based on selected parameters
                truncation = None
                
                if not selected_year and not selected_month and not selected_day:  # All null, aggregate by year and month
                    truncation = TruncMonth('date_time')
                elif selected_year and not selected_month and not selected_day:  # Year selected, aggregate by month
                    truncation = TruncMonth('date_time')
                elif selected_year and selected_month and not selected_day:  # Year and month selected, aggregate by day
                    truncation = TruncDay('date_time')
                elif selected_year and selected_month and selected_day:  # Year, month, and day selected, aggregate by hour
                    truncation = TruncHour('date_time')
                elif selected_day and not selected_year and not selected_month:  # Only day selected, aggregate by matching days across years/months
                    truncation = TruncDay('date_time')
                elif selected_month and not selected_year and not selected_day:  # Only month selected, aggregate by month across years
                    truncation = TruncMonth('date_time')

                if truncation is not None:
                    queryset = CheckoutInfo.objects \
                        .annotate(date=truncation) \
                        .values('date') \
                        .annotate(total=Count('id'))
                else:
            # Handle the case where none of the conditions are met
                    return Response({"error": "Invalid time selection"}, status=400)
                # Fetch and process ScanInfo data
                scan_data = ScanInfo.objects.filter(filters) \
                    .annotate(date=truncation) \
                    .values('date') \
                    .annotate(count=Count('id')) \
                    .order_by('date')

                # Fetch and process CheckoutInfo data
                checkout_data = CheckoutInfo.objects.filter(filters) \
                    .annotate(date=truncation) \
                    .values('date') \
                    .annotate(count=Count('id')) \
                    .order_by('date')

                # Prepare the response data
                data = {
                    'scan_data': list(scan_data),
                    'checkout_data': list(checkout_data),
                }
                cache.set(cache_key, data, timeout=3600)  # Cache for 1 hour
                
                return Response(data)
            return Response({'Error' : 'Company does not exist'}, status=status.HTTP_404_NOT_FOUND)

class BarChartDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        company_name = request.query_params.get('company_name')
        selected_criteria = request.query_params.get('Region')
        selected_range = request.query_params.get('High')
        
        # Ensure company name is provided
        if company_name:
            cache_key = sanitize_cache_key(f"bar_chart_info{company_name}_{selected_criteria}_{selected_range}")
            final_data = cache.get(cache_key)
            
            if not final_data:       
                # Build the query filters to exclude rows with null values in the location fields
                filters = Q(company_name=company_name)
                filters &= Q(country__isnull=False) & Q(region__isnull=False) & Q(city__isnull=False) & Q(town__isnull=False) & Q(street__isnull=False)

                # Aggregate the data based on the selected criteria
                location_field = {
                    'Region': 'region',
                    'City': 'city',
                    'Town': 'town',
                    'Locality': 'street'
                }.get(selected_criteria, 'region')

                # Fetch and aggregate ScanInfo data
                scan_data = ScanInfo.objects.filter(filters) \
                    .values(location_field) \
                    .annotate(scanned_count=Count('id')) \
                    .order_by(location_field)

                # Fetch and aggregate CheckoutInfo data
                checkout_data = CheckoutInfo.objects.filter(filters) \
                    .values(location_field) \
                    .annotate(checkout_count=Count('id')) \
                    .order_by(location_field)

                # Merge the scan_data and checkout_data based on location_field
                aggregated_data = {}
                for entry in scan_data:
                    key = entry[location_field]
                    aggregated_data[key] = {
                        'location': key,
                        'scanned': entry['scanned_count'],
                        'checkout': 0  # Initialize with 0, will update later if present in checkout_data
                    }
                
                for entry in checkout_data:
                    key = entry[location_field]
                    if key in aggregated_data:
                        aggregated_data[key]['checkout'] = entry['checkout_count']
                    else:
                        aggregated_data[key] = {
                            'location': key,
                            'scanned': 0,  # Initialize with 0, will update later if present in scan_data
                            'checkout': entry['checkout_count']
                        }

                # Convert the aggregated data to a list of dictionaries for easy JSON serialization
                aggregated_data_list = list(aggregated_data.values())

                # Sort and slice the data based on the selected range
                sorted_data = sorted(aggregated_data_list, key=lambda x: x['checkout'], reverse=True)
                if selected_range == 'High':
                    final_data = sorted_data[:5]
                else:
                    final_data = sorted_data[-5:][::-1]
                    
                cache.set(cache_key, final_data, timeout=60 * 60)
            return Response(final_data)    
        return Response({'error': 'Company name is required'}, status=status.HTTP_404_NOT_FOUND)
class ProductName(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request, *args, **kwargs):
        company_name = request.query_params.get('company_name')
        try:
            if company_name:
                cache_key = sanitize_cache_key(f"product_names_{company_name}")
                data = cache.get(cache_key)
                if not data:
                    products = LogProduct.objects.filter(company_name=company_name).values_list('product_name', flat=True).distinct()
                    cache.set(cache_key, products, timeout=60 * 60)
                return Response(products, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class ProductMetricsView(APIView):

    def get_cache_key(self, company_name, product_name):
        return sanitize_cache_key(f"product_metrics_{company_name}_{product_name}")

    @method_decorator(cache_page(60 * 5))  # Optional: cache the entire view for 5 minutes
    def get(self, request,*args, **kwargs):
        company_name = request.query_params.get('company_name')
        product_name = request.query_params.get('product_name')
        cache_key = self.get_cache_key(company_name, product_name)
        data = cache.get(cache_key)

        if not data:
            try:

                scan_queryset = ScanInfo.objects.filter(
                company_name__iexact=company_name,
                product_name__iexact=product_name
                ).exclude(
                    Q(country='') | Q(country__isnull=True) |
                    Q(region='') | Q(region__isnull=True) |
                    Q(city='') | Q(city__isnull=True) |
                    Q(town='') | Q(town__isnull=True)
                )
                checkout_queryset = CheckoutInfo.objects.filter(
                    company_name__iexact=company_name,
                    product_name__iexact=product_name
                ).exclude(
                    Q(country='') | Q(country__isnull=True) |
                    Q(region='') | Q(region__isnull=True) |
                    Q(city='') | Q(city__isnull=True) |
                    Q(town='') | Q(town__isnull=True)
                )

                checkout_today = checkout_queryset.annotate(day=TruncDay('date_time')).filter(day=F('day')).aggregate(total=Count('id'))['total'] or 0
                checkout_month = checkout_queryset.annotate(month=TruncMonth('date_time')).filter(month=F('month')).aggregate(total=Count('id'))['total'] or 0
                checkout_year = checkout_queryset.annotate(year=TruncYear('date_time')).filter(year=F('year')).aggregate(total=Count('id'))['total'] or 0
                scan_today = scan_queryset.annotate(day=TruncDay('date_time')).filter(day=F('day')).aggregate(total=Count('id'))['total'] or 0
                scan_month = scan_queryset.annotate(month=TruncMonth('date_time')).filter(month=F('month')).aggregate(total=Count('id'))['total'] or 0
                scan_year = scan_queryset.annotate(year=TruncYear('date_time')).filter(year=F('year')).aggregate(total=Count('id'))['total'] or 0
                acceptance_rate = (checkout_queryset.count() / scan_queryset.count()) * 100 if scan_queryset.count() > 0 else 0
                highest_checkout_per_location = checkout_queryset.values('region', 'city', 'town', 'street').annotate(total=Count('id')).order_by('-total').first()
                total_locations = list(checkout_queryset.values('region', 'city', 'town', 'street').annotate(total=Count('id')).order_by('total'))
                median_location = total_locations[len(total_locations) // 2] if total_locations else None
                lowest_checkout_per_location = checkout_queryset.values('region', 'city', 'town', 'street').annotate(total=Count('id')).order_by('total').first()

                data = {
                    'metrics': {
                        'checkout_today': checkout_today,
                        'checkout_month': checkout_month,
                        'checkout_year': checkout_year,
                        'scan_today': scan_today,
                        'scan_month': scan_month,
                        'scan_year': scan_year,
                        'acceptance_rate': acceptance_rate,
                        'highest_checkout_per_location': highest_checkout_per_location,
                        'median_checkout_per_location': median_location,
                        'lowest_checkout_per_location': lowest_checkout_per_location,
                    }
                }
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data, status=status.HTTP_200_OK)


# Store the private key securely
private_key = None

@csrf_exempt
def get_public_key(request):
    global private_key
    private_key, public_key = generate_rsa_key_pair()
    serialized_public_key = serialize_public_key(public_key)
    return JsonResponse({'public_key': serialized_public_key.decode()})

@csrf_exempt
def encrypt_sensitive_data(request):
    global private_key
    if request.method == 'POST':
        encrypted_session_key = urlsafe_b64decode(request.POST.get('session_key', ''))
        
        # Decrypt the session key with the private key
        session_key = decrypt_session_key(private_key, encrypted_session_key)

        # Encrypt sensitive data
        sensitive_data = "This is very sensitive information"
        encrypted_data = encrypt_data(session_key, sensitive_data)

        # Return encrypted data in base64
        encrypted_data_b64 = urlsafe_b64encode(encrypted_data).decode()
        return JsonResponse({'encrypted_data': encrypted_data_b64})
    return JsonResponse({'error': 'Invalid request'}, status=400)

class UserScanView(APIView):
    permission_classes = [IsAuthenticated, IsUser]
    
    def get(self, request, *args, **kwargs):
        user_name = request.query_params.get('email')
        if user_name:
            cache_key = sanitize_cache_key(f"user_scan_info_{user_name}")
            data = cache.get(cache_key)
            
            if not data:
                filtered_data = ScanInfo.objects.filter(user_name__iexact=user_name
                                                        ).exclude(
                                                            Q(country__isnull=True) | Q(country='') |
                                                            Q(region__isnull=True) | Q(region='') |
                                                            Q(city__isnull=True) | Q(city='')                                                                   
                                                            ).values(
                                                                'company_name', 'product_name', 'batch_number'
                                                            ).annotate(
                                                                frequency=Count('batch_number')
                                                            ).order_by('company_name', 'product_name')
                data = list(filtered_data)
                cache.set(cache_key, data, timeout=60 * 60)
            
            return Response(data, status=status.HTTP_200_OK)
        return Response({'error': 'User email not provided'}, status=status.HTTP_404_NOT_FOUND)
                
class UserCheckoutView(APIView):
    permission_classes = [IsAuthenticated, IsUser]
    
    def get(self, request, *args, **kwargs):
        user_name = request.query_params.get('email')
        if user_name:
            cache_key = sanitize_cache_key(f"user_checkout_info_{user_name}")
            data = cache.get(cache_key)
            
            if not data:
                filtered_data = CheckoutInfo.objects.filter(user_name__iexact=user_name
                                                        ).exclude(
                                                            Q(country__isnull=True) | Q(country='') |
                                                            Q(region__isnull=True) | Q(region='') |
                                                            Q(city__isnull=True) | Q(city='')                                                                   
                                                            ).values(
                                                                'company_name', 'product_name', 'batch_number'
                                                            ).order_by('company_name')
                data = list(filtered_data)
                cache.set(cache_key, data, timeout=60 * 60)
            
            return Response(data, status=status.HTTP_200_OK)
        return Response({'error': 'User email not provided'}, status=status.HTTP_404_NOT_FOUND)
                