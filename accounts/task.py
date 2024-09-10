from celery import shared_task
from django.utils import timezone
from .models import Company
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@shared_task
def delete_unverified_user(user_id):
    logger.info("I have started")
    user = Company.objects.get(id=user_id)
    logger.info(f"Unverified user: {user}")
    if not user.is_verified and (timezone.now() - user.created_at).total_seconds() > 420:  # 15 minutes = 900 seconds
        user.delete()
        logger.info(f"Deleted user: {user}")
        
