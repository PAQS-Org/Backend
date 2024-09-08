from celery import shared_task
from django.utils import timezone
from .models import Company

@shared_task
def delete_unverified_user(user_id):
    user = Company.objects.get(id=user_id)
    if not user.is_verified and (timezone.now() - user.created_at).total_seconds() > 900:  # 15 minutes = 900 seconds
        user.delete()
