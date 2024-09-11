from celery import shared_task
from django.utils import timezone
from .models import Company
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@shared_task
def delete_unverified_user(user_id):
    logger.info("Started deleting unverified user")
    try:
        user = Company.objects.get(id=user_id)
        logger.info(f"Unverified user: {user}")
        logger.info(f"User is_verified: {user.is_verified}")
        
        time_diff = (timezone.now() - user.created_at).total_seconds()
        logger.info(f"Time difference since user creation (in seconds): {time_diff}")
        
        if not user.is_verified and time_diff > 300:
            user.delete()
            logger.info(f"Deleted user: {user}")
        else:
            logger.info(f"User not deleted: Condition not met (is_verified={user.is_verified}, time_diff={time_diff})")
            
    except Company.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
