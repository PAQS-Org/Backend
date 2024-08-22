from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ProductsInfo, LogProduct, ScanInfo
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsOwner, IsUser
from .serializer import CheckoutInfoSerializer, ScanInfoSerializer
from .task import scan_process_location, checkout_process_location, hierarchical_search
from django.db import IntegrityError

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

     





