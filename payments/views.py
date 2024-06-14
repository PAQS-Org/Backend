from django.shortcuts import render
import requests

# Create your views here.
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt  # Handle POST requests securely
from io import BytesIO
import json
import hmac
import hashlib
from django.http import FileResponse
from .models import Payment 
from .serializer import PaymentSerializer
from accounts.models import Company
from rest_framework.permissions import IsAuthenticated
from .permissions import IsOwner
from .prices import calculate_unit_price
from PAQSBackend.settings import PAYSTACK_SECRET_KEY
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from weasyprint import HTML


class InitiatePayment(APIView):
    serializer_class = PaymentSerializer
    permission_classes = (IsAuthenticated, IsOwner)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_data = serializer.data
        product_name = user_data.get('product_name')
        quantity = user_data.get('quantity')
        (amount, _, unit_price) = calculate_unit_price(quantity)

        comp = Company.objects.get(email=request.user)


        headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
        payload = {
            "amount": amount * 100,
            "email": request.user.email,
            "currency": "GHS",
        }

        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            json=payload,
            headers=headers,
        )
        data = response.json()

        # Save transaction details to the database
        transaction = Payment.objects.create(
                    company = comp,
                    quantity=quantity,
                    amount=amount,
                    product_name=product_name,
                    unit_price=unit_price,
                    transaction_id=data.get('data', {}).get('reference'),
                    )
        return JsonResponse({"payment_url": data["data"]["authorization_url"]})


@csrf_exempt
def verify_payment(request):
  # Get the request body content
  hook = request.body.decode('utf-8')
  hook_data = hook.strip()

  # Verify the request signature using HMAC
  signature = request.headers['x-paystack-signature']
  computed_signature = hmac.new(
                PAYSTACK_SECRET_KEY.encode('utf-8'),
                hook_data.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()
  if not hmac.compare_digest(computed_signature, signature):
      return HttpResponse("Signature verification failed.", status=400)

  # Parse the request data
  try:
      data = json.loads(hook_data)
  except json.JSONDecodeError:
      return HttpResponse("Invalid JSON payload", status=400)

  # Check for the event type
  event = data.get('event')
  if event != 'charge.success':
      return HttpResponse("Only charge.success event is processed.", status=400)

  # Retrieve transaction details from the data
  reference = data['data']['reference']
  transaction_id = data['data']['id']

  try:
      # Update the transaction status in your database
      payment = Payment.objects.get(transaction_id=reference)
      payment.transaction_status = 'paid'
      payment.verified = True 
      payment.save()
  except Payment.DoesNotExist:
      return HttpResponse("Transaction not found.", status=400)

  # Return a successful response
  return HttpResponse("Transaction updated successfully.", status=200)



def download_receipt(request, reference):
    try:
        transaction = Payment.objects.get(transaction_id=reference)
    except Payment.DoesNotExist:
        return HttpResponse("Transaction not found", status=404)

    receipt_html = f"""
    <html>
    <body>
        <h1>Receipt</h1>
        <p>Product Name: {transaction.product_name}</p>
        <p>Quantity: {transaction.quantity}</p>
        <p>Amount: GHS {transaction.amount}</p>
        <p>Transaction Reference: {transaction.transaction_id}</p>
        <p>Date: {transaction.date_created}</p>
        <p>Company: {transaction.company.name_of_company}</p>
    </body>
    </html>
    """

    html = HTML(string=receipt_html)
    pdf_file = html.write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=receipt_{reference}.pdf'
    
    return response


def delete_old_transactions():
  # Schedule this task to run periodically (e.g., using Celery or cron)
  threshold = timezone.now() - timezone.timedelta(days=30)
  transactions = Payment.objects.filter(created_at__lt=threshold, transaction_status__in=["failed", "pending"])
  transactions.delete()


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        company = self.request.user.company
        return Payment.objects.filter(company=company)  