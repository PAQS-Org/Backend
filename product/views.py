from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import LogProduct, ScanInfo, CheckoutInfo
from django.db.models import Count, Avg, F,Q
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsOwner, IsUser
from .serializer import CheckoutInfoSerializer, ScanInfoSerializer, LogProductSerializer
from .task import scan_process_location, checkout_process_location, hierarchical_search
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
import logging
from smtplib import SMTPException
from django.core.cache import cache
from django.utils import timezone
import datetime
import calendar

@method_decorator(csrf_exempt, name='dispatch')
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
            status_code = search_result.get('status', status.HTTP_200_OK)

            if ScanInfo.objects.filter(
                code_key__iexact=code_key,
                company_name__iexact=company_name,
                product_name__iexact=product_name,
                batch_number__iexact=batch_number,
                user_name__iexact=email
            ).exists():
                return Response({
                    'message': message, 
                    'company_name':company_name,
                    'product_name':product_name,
                    'batch_number':batch_number,
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
                # Process location asynchronously
                scan_process_location(scan_info.location, serializer)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Return the message after storing the scan information
            return Response({
                    'message': message, 
                    'company_name':company_name,
                    'product_name':product_name,
                    'batch_number':batch_number,
                    }, status=status_code)

        except LogProduct.DoesNotExist:
            return Response({'message': 'Last part of the code not found'}, status=status.HTTP_404_NOT_FOUND)


@method_decorator(csrf_exempt, name='dispatch')
class CheckoutInfoView(APIView):
    permission_classes = (IsAuthenticated, IsUser, IsOwner)
    serializer_class = CheckoutInfoSerializer  # Assuming ScanInfoSerializer will be used for storing checkout information as well

    def post(self, request):
        qr_code = request.data.get('qr_code')
        email = request.data.get('email')
        location = request.data.get('location')
        print('i have started')
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
                print('checkout to db', checkout_data)
                serializer = self.serializer_class(data=checkout_data, context={'request': request})
                print('ser to db', serializer)
                print('ser val', serializer.is_valid())
                print('ser err', serializer.errors)
                if serializer.is_valid():
                    checkout_info = serializer.save()
                    # Process location asynchronously
                    checkout_process_location(checkout_info.location, serializer)

                # Return the checkout message
                return Response({'message': log_product.checkout_message}, status=status.HTTP_200_OK)

            except LogProduct.DoesNotExist:
                return Response({'message': 'Product does not exist'}, status=status.HTTP_404_NOT_FOUND)

        except ValueError:
            return Response({'message': 'Invalid QR code format'}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')    
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
        subject = f"Product Update: {log_product.product_name} of {log_product.batch_number}"
        message = (
            f"Hello,\n\n"
            f"{log_product.company_name} has updated the information for {log_product.product_name} "
            f"of batch number {log_product.batch_number} with the following message:\n\n"
            f"\"{log_product.patch_message}\"\n\n"
            f"Please take note of the message and its necessary instructions.\n\n"
            f"Best regards,\n"
            f"Your Company"
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

    def get(self, request, *args, **kwargs):
        company_name = request.query_params.get('company_name')
        if company_name:

            cache_key = f"scan_metrics_{company_name}"
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
                ) * 100 if rows_day_before_yesterday > 0 else None

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
                ) * 100 if rows_last_year > 0 else None

                data = {
                    "scan_total_rows": total_rows,
                    "scan_current_month_name": calendar.month_name[datetime.date.today().month],
                    "scan_rows_current_month": rows_current_month,
                    "scan_growth_rate_previous_day": growth_rate_previous_day,
                    "scan_annual_growth_rate": annual_growth_rate
                }
                print('final', data)
                cache.set(cache_key, data, timeout=3600)

            return Response(data)
        return Response({'message': "Company doesn't exist"}, status=status.HTTP_404_NOT_FOUND)
    

class CheckoutMetricsView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request, *args, **kwargs):
        company_name = request.query_params.get('company_name')
        if company_name:

            cache_key = f"checkout_metrics_{company_name}"
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
                ) * 100 if rows_day_before_yesterday > 0 else None
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
                ) * 100 if rows_last_year > 0 else None

                data = {
                    "total_rows": total_rows,
                    "current_month_name": calendar.month_name[datetime.date.today().month],
                    "rows_current_month": rows_current_month,
                    "growth_rate_previous_day": growth_rate_previous_day,
                    "annual_growth_rate": annual_growth_rate
                }
                

                cache.set(cache_key, data, timeout=3600)

            return Response(data)
        return Response({'message': "Company doesn't exist"}, status=status.HTTP_404_NOT_FOUND)
    


class TopLocationMetrics(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        company_name = request.query_params.get('company_name')
        if company_name:
            cache_key = f"location_metrics_comparison_{company_name}"
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
                print('final', data)

                cache.set(cache_key, data, timeout=3600)  # Cache for 1 hour

            return Response(data)
        return Response({'message': "Company doesn't exist"}, status=status.HTTP_404_NOT_FOUND)




class PerformanceMetricsView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request, *args, **kwargs):
        company_name = request.data.get('company_name')  # Assuming the user model has a company_name field
        cache_key = f"performance_metrics_{company_name}"
        data = cache.get(cache_key)

        if not data:
            # 1. Conversion rate calculation
            total_scans = ScanInfo.objects.filter(company_name__iexact=company_name).count()
            total_checkouts = CheckoutInfo.objects.filter(company_name=company_name).count()
            conversion_rate = (total_checkouts / total_scans) * 100 if total_scans > 0 else 0

            # 2. Month and year with the highest checkout
            checkout_by_month = CheckoutInfo.objects.filter(company_name__iexact=company_name).annotate(
                year=F('date_time__year'),
                month=F('date_time__month')
            ).values('year', 'month').annotate(
                checkout_count=Count('id')
            ).order_by('-checkout_count').first()

            if checkout_by_month:
                highest_checkout_month = f"{checkout_by_month['month']}, {checkout_by_month['year']}"
                highest_checkout_month_value = checkout_by_month['checkout_count']
            else:
                highest_checkout_month = None
                highest_checkout_month_value = 0

            data = {
                "conversion_rate": conversion_rate,
                "highest_checkout_month": highest_checkout_month,
                "highest_checkout_month_value": highest_checkout_month_value,
            }

            # Cache the results
            cache.set(cache_key, data, timeout=3600)  # Cache for 1 hour

        return Response(data)