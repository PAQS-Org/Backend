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
        x,y,z,code_key, company_name, product_name, batch  = qr_code.split('/')
        batch_number = batch[:-1]
        print('post code_key', code_key)
        print('post company_name', company_name)
        print('post product_name', product_name)
        print('post batch_number', batch_number)
        print('post qr_code', qr_code)

        # Hierarchical search in LogProduct table
        try:
            search_result = hierarchical_search(company_name, product_name, batch_number, code_key)
            print('hierachical search result', search_result)
            # result = search_result.get(timeout=5000)
            result = search_result
            # Store the scan information in the database
            
            scan_data = {
                'code_key': code_key,
                'company_name': company_name,
                'product_name': product_name,
                'batch_number':batch_number,
                'user_name': email,
                'location': location,
            }

            print('scan data', scan_data)

            serializer = self.serializer_class(data=scan_data, context={'request': request})
            print('scan data to serializer', serializer)
            if serializer.is_valid():
                scan_info = serializer.save()
                # Process location asynchronously
                print('scan info to location', scan_info)
                scan_process_location(scan_info.id)

            return Response({'message': result}, status=status.HTTP_200_OK)
        
        except LogProduct.DoesNotExist:
            return Response({'message': 'Last part of the code not found'}, status=status.HTTP_404_NOT_FOUND)
        

class CheckoutInfoView(APIView):
    permission_classes = (IsAuthenticated, IsUser)

    def post(self, request):
        data = request.data
        task = checkout_process_location.delay(data)
        return Response({'task_id': task.id}, status=status.HTTP_202_ACCEPTED)





