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
from product.models import LogProduct
from product.serializer import LogProductSerializer
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsOwner
from .prices import calculate_unit_price
from PAQSBackend.settings import PAYSTACK_SECRET_KEY
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
# from weasyprint import HTML
from django.template.loader import render_to_string
from django.templatetags.static import static
from .lib.generator import generate
from .lib.messages import prodmessage


class InitiatePayment(APIView):
    serializer_class = PaymentSerializer
    permission_classes = (IsAuthenticated, IsOwner)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_data = serializer.data
        print("user data", user_data)
        # Extract necessary data
        product_name = user_data.get('product_name')
        batch_number = user_data.get('batch_number')
        prod_logo = user_data.get('product_logo')
        perish = user_data.get('perishable')
        manu_date = user_data.get('manufacture_date')
        exp_date = user_data.get('expiry_date')
        qr_type = user_data.get('render_type')
        quantity = user_data.get('quantity')
        amount, _, unit_price = calculate_unit_price(quantity)

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
            company=comp,
            quantity=quantity,
            amount=amount,
            perishable=perish,
            product_logo=prod_logo,
            render_type=qr_type,
            manufacture_date=manu_date,
            expiry_date=exp_date,
            product_name=product_name,
            batch_number=batch_number,
            unit_price=unit_price,
            transaction_id=data.get('data', {}).get('reference'),
        )
        print("transaction:", transaction)
        return JsonResponse({"payment_url": data["data"]["authorization_url"]})


@csrf_exempt
def verify_payment(request):
    hook = request.body.decode('utf-8')
    signature = request.headers.get('x-paystack-signature')

    # Verify the signature
    computed_signature = hmac.new(
        PAYSTACK_SECRET_KEY.encode('utf-8'),
        hook.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()

    if not hmac.compare_digest(computed_signature, signature):
        return HttpResponse("Signature verification failed.", status=400)

    try:
        data = json.loads(hook)
    except json.JSONDecodeError:
        return HttpResponse("Invalid JSON payload", status=400)

    event = data.get('event')
    reference = data['data']['reference']

    try:
        payment = Payment.objects.get(transaction_id=reference)
        if event == 'charge.success':
            payment.transaction_status = 'paid'
            payment.verified = True
            payment.save()

            make_qr = generate(count=payment.quantity, format=payment.render_type, comp=payment.company, prod=payment.product_name, logo=payment.product_logo)

            log_entries = [
                LogProduct(
                    company_name=payment.company,
                    product_name=payment.product_name,
                    batch_code=payment.batch_number,
                    qr_key=make_qr[n], 
                    perishable=payment.perishable,
                    manufacture_date=payment.manufacture_date,
                    expiry_date=payment.expiry_date,
                    message=prodmessage(company=payment.company, product=payment.product_name, perish=payment.perishable, man_date=payment.manufacture_date, exp_date=payment.expiry_date)
                )
                for n in range(payment.quantity)
            ]
            LogProduct.objects.bulk_create(log_entries)
        else:
            payment.transaction_status = data['data']['status']  # Assuming status is available in the payload
            payment.verified = False
            payment.save()

    except Payment.DoesNotExist:
        return HttpResponse("Transaction not found.", status=400)

    return HttpResponse("Transaction updated successfully.", status=200)



# def download_receipt(request, transaction_id):
#     try:
#         transaction = Payment.objects.get(transaction_id=transaction_id)
#     except Payment.DoesNotExist:
#         return HttpResponse("Transaction not found", status=404)

#     logo_url = request.build_absolute_uri(static('images/logo.png'))
#     receipt_html = render_to_string('receipt.html',{
#         'trans_ref':transaction.transaction_id,
#         'date':transaction.date_created,
#         'prod_name':transaction.product_name,
#         'comp_name':transaction.company.company_name,
#         'batch_num':transaction.batch_number,
#         'unit_price':transaction.unit_price,
#         'qty':transaction.quantity,
#         'total':transaction.amount,
#         'logo_url': logo_url,
#     }) 
   

#     html = HTML(string=receipt_html)
#     pdf_file = html.write_pdf()

#     response = HttpResponse(pdf_file, content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename=receipt_{transaction_id}.pdf'
    
#     return response


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
    
class CheckPaymentStatus(APIView):
    def get(self, request, reference):
        try:
            payment = Payment.objects.get(transaction_id=reference)
            return JsonResponse({
                'status': payment.transaction_status,
                'verified': payment.verified
            })
        except Payment.DoesNotExist:
            return JsonResponse({'error': 'Transaction not found'}, status=404)