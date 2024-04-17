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





# @csrf_exempt
# def verify_payment(request):
#     # retrive the payload from the request body
#     payload = request.body
#     # signature header to to verify the request is from paystack
#     sig_header = request.headers['x-paystack-signature']
#     body = None
#     event = None

#     try:
#         # sign the payload with `HMAC SHA512`
#         hash = hmac.new(PAYSTACK_SECRET_KEY.encode('utf-8'), payload, digestmod=hashlib.sha512).hexdigest()
#         # compare our signature with paystacks signature
#         if hash == sig_header:
#             # if signature matches, 
#             # proceed to retrive event status from payload
#             body_unicode = payload.decode('utf-8')
#             body = json.loads(body_unicode)
#             # event status
#             event = body['event']
#         else:
#             raise Exception
#     except ValueError as e:
#         # Invalid payload
#         return HttpResponse(status=400)
#     except KeyError as e:
#         # Invalid payload
#         return HttpResponse(status=400)
#     except:
#         # Invalid signature
#         return HttpResponse(status=400)

#     if event == 'charge.success':
#         # if event status equals 'charge.success'
#         # get the data and the `payment_id` 
#         # we'd set in the metadata ealier
#         data, transaction_id = body["data"], body['data']['metadata']['transaction_id']

#         # validate status and gateway_response
#         if (data["status"] == 'success') and (data["gateway_response"] == "Successful"):
#             try:
#                 payment = Payment.objects.get(id=transaction_id)
#             except Payment.DoesNotExist:
#                 return HttpResponse(status=404)
#             # mark payment as paid
#             payment.verified = True
#             payment.save(force_update=True)

#             print("PAID")

#     return HttpResponse(status=200)


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