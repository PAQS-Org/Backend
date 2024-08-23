from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import LogProduct, ScanInfo, CheckoutInfo
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsOwner, IsUser
from .serializer import CheckoutInfoSerializer, ScanInfoSerializer, LogProductSerializer
from .task import scan_process_location, checkout_process_location, hierarchical_search
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
import logging
from smtplib import SMTPException
from django.core.cache import cache
from django.db.models import Count, Avg, F, ExpressionWrapper, fields
from django.utils import timezone
import datetime

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
        company_name = request.data.get('company_name')  # Assuming the user model has a company_name field
        cache_key = f"scan_metrics_{company_name}"
        data = cache.get(cache_key)

        if not data:
            # Filter data by company and exclude rows with empty fields
            filtered_data = ScanInfo.objects.filter(
                company_name=company_name
            ).exclude(
                country='',
                region='',
                city=''
            )

            # Total number of rows
            total_rows = filtered_data.count()

            # Sum of rows for the prevailing month
            current_month = timezone.now().month
            rows_current_month = filtered_data.filter(
                date_time__month=current_month
            ).count()

            # Average data received from the beginning of the year to the previous day of the current day
            current_year = timezone.now().year
            yesterday = timezone.now().date() - datetime.timedelta(days=1)
            average_data_ytd = filtered_data.filter(
                date_time__year=current_year,
                date_time__lt=yesterday
            ).aggregate(avg=Avg('date_time'))['avg']

            # Average data received per day
            days_since_first_entry = (timezone.now().date() - filtered_data.earliest('date_time').date_time).days
            average_per_day = total_rows / days_since_first_entry if days_since_first_entry > 0 else total_rows

            data = {
                "total_rows": total_rows,
                "rows_current_month": rows_current_month,
                "average_data_ytd": average_data_ytd,
                "average_per_day": average_per_day
            }

            cache.set(cache_key, data, timeout=3600)  

        return Response(data)
    

class CheckoutMetricsView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request, *args, **kwargs):
        company_name = request.data.get('company_name')  # Assuming the user model has a company_name field
        cache_key = f"checkout_metrics_{company_name}"
        data = cache.get(cache_key)

        if not data:
            filtered_data = CheckoutInfo.objects.filter(
                company_name=company_name
            ).exclude(
                country='',
                region='',
                city=''
            )
            print('f_data', filtered_data)

            total_rows = filtered_data.count()
            current_month = timezone.now().month
            rows_current_month = filtered_data.filter(
                date_time__month=current_month
            ).count()
            current_year = timezone.now().year
            yesterday = timezone.now().date() - datetime.timedelta(days=1)
            
            print('row', total_rows)
            print('c_month', current_month)
            print('c_year', current_year)
            print('yest', yesterday)
            print('row_c_month', rows_current_month)
            # Convert date_time to a Unix timestamp (seconds since the epoch)
            average_timestamp_ytd = filtered_data.filter(
                date_time__year=current_year,
                date_time__lt=yesterday
            ).annotate(
                timestamp=ExpressionWrapper(F('date_time'), output_field=fields.FloatField())
            ).aggregate(avg_timestamp=Avg('timestamp'))['avg_timestamp']
            print('avg tmstp', average_data_ytd)

            if average_timestamp_ytd:
                # Convert the average timestamp back to a datetime object
                average_data_ytd = datetime.datetime.fromtimestamp(average_timestamp_ytd, tz=timezone.utc)
            else:
                average_data_ytd = None

            days_since_first_entry = (timezone.now().date() - filtered_data.earliest('date_time').date_time.date()).days
            average_per_day = total_rows / days_since_first_entry if days_since_first_entry > 0 else total_rows

            data = {
                "total_rows": total_rows,
                "rows_current_month": rows_current_month,
                "average_data_ytd": average_data_ytd,
                "average_per_day": average_per_day
            }
            print('final', data)

            cache.set(cache_key, data, timeout=3600)  

        return Response(data)
    

class TopLocationMetrics(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request, *args, **kwargs):
        company_name = request.data.get('company_name')  # Assuming the user model has a company_name field
        cache_key = f"metrics_comparison_{company_name}"
        data = cache.get(cache_key)

        if not data:
            # Common function to get location with highest and lowest counts
            def get_location_metrics(queryset, location_fields):
                location_data = queryset.values(*location_fields).annotate(count=Count('id'))
                highest_location = location_data.order_by('-count').first()
                lowest_location = location_data.order_by('count').first()
                return highest_location, lowest_location

            # Locations to consider in the order
            location_fields = ['country', 'region', 'city', 'town']

            # ScanInfo Metrics
            scan_queryset = ScanInfo.objects.filter(company_name=company_name).exclude(
                country='',
                region='',
                city='',
                town='',
            )
            highest_scan_location, lowest_scan_location = get_location_metrics(scan_queryset, location_fields)

            # CheckoutInfo Metrics
            checkout_queryset = CheckoutInfo.objects.filter(company_name=company_name).exclude(
                country='',
                region='',
                city='',
                town='',
            )
            highest_checkout_location, lowest_checkout_location = get_location_metrics(checkout_queryset, location_fields)

            # Product with the highest checkout
            highest_checkout_product = checkout_queryset.values('product_name').annotate(total=Count('id')).order_by('-total').first()

            data = {
                "highest_scan_location": highest_scan_location,
                "lowest_scan_location": lowest_scan_location,
                "highest_checkout_location": highest_checkout_location,
                "lowest_checkout_location": lowest_checkout_location,
                "highest_checkout_product": highest_checkout_product
            }

            # Cache the results
            cache.set(cache_key, data, timeout=3600)  # Cache for 1 hour

        return Response(data)
    

class PerformanceMetricsView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request, *args, **kwargs):
        company_name = request.data.get('company_name')  # Assuming the user model has a company_name field
        cache_key = f"performance_metrics_{company_name}"
        data = cache.get(cache_key)

        if not data:
            # 1. Conversion rate calculation
            total_scans = ScanInfo.objects.filter(company_name=company_name).count()
            total_checkouts = CheckoutInfo.objects.filter(company_name=company_name).count()
            conversion_rate = (total_checkouts / total_scans) * 100 if total_scans > 0 else 0

            # 2. Month and year with the highest checkout
            checkout_by_month = CheckoutInfo.objects.filter(company_name=company_name).annotate(
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