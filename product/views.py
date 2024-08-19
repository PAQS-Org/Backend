from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ProductsInfo, LogProduct
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsOwner, IsUser
from .serializer import ProductInfoSerializer, LogProductSerializer, ScanInfoSerializer
from .task import scan_process_location, checkout_process_location, hierarchical_search

class CreateProductItems(APIView):
  permission_classes = (IsAuthenticated, IsOwner)
  def post(self, request):
    data_list = request.data.get('items', [])  # Assuming 'items' is the key in request data
    order_items = []
    for item in data_list:
      serializer = ProductInfoSerializer(data=item)
      if serializer.is_valid():
        order_item = serializer.save()
        order_items.append(order_item)
      else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response({"message": "Order items created successfully", "data": ProductInfoSerializer(order_items, many=True).data})


@method_decorator(csrf_exempt, name='dispatch')
class ScanInfoView(APIView):
    permission_classes = (IsAuthenticated, IsUser, IsOwner)
    serializer_class = ScanInfoSerializer

    def post(self, request):
        # Parse QR code data
        qr_code = request.data.get('qr_code')
        email = request.data.get('email')
        location = request.data.get('location')
        _, code_key, company_name, product_name, batch_number  = qr_code.split('/')

        # Hierarchical search in LogProduct table
        try:
            search_result = hierarchical_search.delay(company_name, product_name, batch_number, code_key)
            result = search_result.get(timeout=10)
            # Store the scan information in the database
            
            scan_data = {
                'code_key': code_key,
                'company_name': company_name,
                'product_name': product_name,
                'user_name': email,
                'location': location,
            }

            serializer = self.serializer_class(data=scan_data, context={'request': request})
            if serializer.is_valid():
                scan_info = serializer.save()
                # Process location asynchronously
                scan_process_location.delay(scan_info.id)

            return Response({'message': result}, status=status.HTTP_200_OK)
        
        except LogProduct.DoesNotExist:
            return Response({'message': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        

class CheckoutInfoView(APIView):
    permission_classes = (IsAuthenticated, IsUser)

    def post(self, request):
        data = request.data
        task = checkout_process_location.delay(data)
        return Response({'task_id': task.id}, status=status.HTTP_202_ACCEPTED)





