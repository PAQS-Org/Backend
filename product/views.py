from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ProductsInfo
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsOwner, IsUser
from .serializer import ProductInfoSerializer
from .task import scan_process_location, checkout_process_location

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
