import requests

# Create your views here.
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt  
import json
import hmac
import hashlib
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from .models import Payment 
from .serializer import PaymentSerializer
from product.models import LogProduct
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsOwner
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
import boto3
from django.conf import settings
from django.core.cache import cache
import logging

# Set up the logger
logger = logging.getLogger('django')

class InitiatePayment(APIView):
    serializer_class = PaymentSerializer
    permission_classes = (IsAuthenticated, IsOwner)

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        payment_instance = serializer.save()
        print(payment_instance)
        headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
        payload = {
            "amount": payment_instance.amount * 100,
            "email": request.user.email,
            "currency": "GHS",
        }

        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            json=payload,
            headers=headers,
        )
        data = response.json()
        payment_instance.transaction_id = data.get('data', {}).get('reference')
        payment_instance.save()

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

            gen = generate.delay(count=payment.quantity, batch=payment.batch_number, format=payment.render_type, comp=payment.company, prod=payment.product_name, logo=payment.product_logo)
            s3_url, make_qr, gen_id = gen.get() 
            print('s3_url', s3_url)
            log_entries = [
                LogProduct(
                    company_code=payment.company,
                    product_code=payment.product_name,
                    batch_code=payment.batch_number,
                    qr_key=gen_id, 
                    perishable=payment.perishable,
                    manufacture_date=payment.manufacture_date,
                    expiry_date=payment.expiry_date,
                    message=prodmessage(
                        company=payment.company, 
                        product=payment.product_name, 
                        batch=payment.batch_number, 
                        perish=payment.perishable, 
                        man_date=payment.manufacture_date, 
                        exp_date=payment.expiry_date
                        )
                )
                for gen_id, _ in make_qr 
            ]

            LogProduct.objects.bulk_create(log_entries)
            payment.QRcode_status = 'completed'
            payment.file_id = gen_id
            payment.save()
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
    
class QRCodeViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        company = self.request.user.company
        return Payment.objects.filter(company=company, QRcode_status='completed')

    
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
        

def generate_presigned_url(company_name, product_name, batch_number, uuid, expiration=3600):
    file_key = f"static/qrcodes/{company_name}/{product_name}/{batch_number}_{uuid}.zip"
    s3_client = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                  aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                  region_name=settings.AWS_S3_REGION_NAME)
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                                            'Key': file_key},
                                                    ExpiresIn=expiration)
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        return None
    return response


def get_cached_presigned_url(company_name, product_name, batch_number, uuid):
    cache_key = f"{company_name}/{product_name}/{batch_number}_{uuid}"
    url = cache.get(cache_key)
    if not url:
        url = generate_presigned_url(company_name, product_name, batch_number, uuid)
        cache.set(cache_key, url, timeout=3600)  # Cache for 1 hour
    return url

@login_required
def get_user_file(request, company_name, product_name, batch_number, uuid):
    user = request.user    
    presigned_url = get_cached_presigned_url(company_name, product_name, batch_number, uuid)
    if presigned_url:
        log_file_access(user, company_name, product_name, batch_number, uuid)
        return JsonResponse({'url': presigned_url})
    return JsonResponse({'error': 'Could not generate URL'}, status=400)


def log_file_access(user, company_name, product_name, batch_number, uuid):
    logger.info(f"User {user.username} accessed {company_name}/{product_name}/{batch_number}_{uuid}.zip")
