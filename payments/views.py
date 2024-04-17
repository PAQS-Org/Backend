from django.shortcuts import render
import requests
from django.contrib.auth.decorators import login_required

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



def verify_webhook_signature(request):
  if request.method != 'POST':
    return JsonResponse({'error': 'Method not allowed'}, status=405)

  signature = request.META.get("HTTP_X-PAYSTACK-SIGNATURE")
  payload = request.body.decode("utf-8")
  hashed_payload = hmac.new(
    PAYSTACK_SECRET_KEY.encode("utf-8"), msg=payload, digestmod=hashlib.sha256
  ).hexdigest()
  return signature.lower() == hashed_payload.lower()


@csrf_exempt
def verify_payment(request):
    if request.method == "POST":
        # Retrieve and verify the signature from Paystack's webhook
        data = request.POST

        # Retrieve transaction details using the transaction ID
        transaction_id = data.get("data")
        try:
            transaction = Payment.objects.get(transaction_id=transaction_id)
        except Payment.DoesNotExist:
            return JsonResponse({"message": "Transaction not found"}, status=400)

        # Update transaction status based on Paystack response
        if data.get("data")["status"] == "success":
            transaction.transaction_status = "success"
            transaction.save()
            # Redirect to success step on frontend (handled in success callback)
            return JsonResponse({"message": "Payment successful"})
        else:
            transaction.transaction_status = "failed"
            transaction.save()
            # Redirect to failure step on frontend (handled in error callback)
            return JsonResponse({"message": "Payment failed"})
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


def download_receipt(request, reference):
    try:
        transaction = Payment.objects.get(reference=reference)
    except Payment.DoesNotExist:
        return HttpResponse("Transaction not found", status=404)

    # Generate receipt content (e.g., using a templating library)
    receipt_content = f"""
  Product Name: {transaction.product_name}
  Quantity: {transaction.quantity}
  Amount: GHS {transaction.amount}
  Transaction Reference: {transaction.reference}
  Date: {transaction.date_created}
  Company: {transaction.company.name_of_company}  # Add company name
  """

    # Create a file-like object for the receipt
    buffer = BytesIO(receipt_content.encode("utf-8"))

    # Set response headers for file download
    response = FileResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename=receipt_{reference}.pdf"

    return response


def delete_old_transactions():
  # Schedule this task to run periodically (e.g., using Celery or cron)
  threshold = timezone.now() - timezone.timedelta(days=30)
  transactions = Payment.objects.filter(created_at__lt=threshold, transaction_status__in=["failed", "pending"])
  transactions.delete()