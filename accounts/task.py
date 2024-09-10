from celery import shared_task
from django.utils import timezone
from .models import Company

@shared_task
def delete_unverified_user(user_id):
    print("I have started")
    user = Company.objects.get(id=user_id)
    print("unverf user", user)
    if not user.is_verified and (timezone.now() - user.created_at).total_seconds() > 420:  # 15 minutes = 900 seconds
        user.delete()
