from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ProductsInfo
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsOwner, IsUser
from .serializer import ProductInfoSerializer, LogProductSerializer
from .task import scan_process_location, checkout_process_location
from .lib.generator import generate
from .lib.messages import prodmessage


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


class ScanInfoView(APIView):
    permission_classes = (IsAuthenticated, IsUser)

    def post(self, request):
        data = request.data
        task = scan_process_location.delay(data)
        return Response({'task_id': task.id}, status=status.HTTP_202_ACCEPTED)


class CheckoutInfoView(APIView):
    permission_classes = (IsAuthenticated, IsUser)

    def post(self, request):
        data = request.data
        task = checkout_process_location.delay(data)
        return Response({'task_id': task.id}, status=status.HTTP_202_ACCEPTED)


class GenerateAndLogQR(APIView):
   permission_classes = (IsAuthenticated, IsOwner)
   serializer_class = LogProductSerializer

   def post(self, request):
      serializer = self.serializer_class(data=request.data)
      serializer.is_valid(raise_exception=True)
      item_data = serializer.data
      company_name = item_data.get('company_name')
      product_name = item_data.get('product_name')
      product_logo = item_data.get('product_logo')
      batch_number = item_data.get('batch_number')
      perish = item_data.get('perish')
      manu_date = item_data.get('manu_date')
      exp_date = item_data.get('exp_date')
      qr_type = item_data.get('qr_type')
      quantity = item_data.get('quantity')
      make_qr = generate(count=quantity, format=qr_type, comp=company_name, prod=product_name, logo=product_logo)

      log_entries = []

      for n in range(quantity):
         qr_code_path = make_qr[n]

         log_entry = LogProductSerializer(
                company_name=company_name,
                product_name=product_name,
                batch_code=batch_number,
                qr_key=qr_code_path,  # Store the path or identifier of the QR code
                message=prodmessage(company=company_name, product=product_name, perish=perish, man_date=manu_date, exp_date=exp_date)
            )
         log_entries.append(log_entry)
        
      LogProductSerializer.objects.create(log_entry)
      
      return Response({"message": f"{quantity} QR codes generated and logged successfully."}, status=status.HTTP_201_CREATED)


