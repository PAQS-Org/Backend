from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ProductsInfo
from rest_framework.permissions import AllowAny
from .serializer import ProductInfoSerializer

class CreateProductItems(APIView):
  permission_classes = AllowAny
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
