from celery import shared_task
from product.models import LogProduct
from .lib.generator import generate
from .lib.messages import prodmessage
from django.http import HttpResponse
from django.core.cache import cache

@shared_task
def generate_qr_codes(payment_id):
    from .models import Payment  # Import here to avoid circular imports
    print("generate begins")
    try:
        payment = Payment.objects.get(transaction_id=payment_id)
        print('payment', payment)
        # Create a unique cache key based on the payment details
        cache_key = f"qr_codes_{payment.transaction_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            s3_url, qr_data = cached_data
        else:
            s3_url, qr_data = generate(
                count=payment.quantity,
                batch=payment.batch_number,
                format=payment.render_type,
                comp=payment.company,
                prod=payment.product_name,
                logo=payment.product_logo
            )
            # Cache the generated data for a certain period (e.g., 24 hours)
            cache.set(cache_key, (s3_url, qr_data), timeout=86400)
        
        log_entries = [
            LogProduct(
                company_name=payment.company,
                product_name=payment.product_name,
                batch_number=payment.batch_number,
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
            for gen_id, _ in qr_data 
        ]
        print('hit the db')
        LogProduct.objects.bulk_create(log_entries)
        payment.QRcode_status = 'completed'
        payment.save()

    except Payment.DoesNotExist:
        return HttpResponse("Transaction not found.", status=400)
