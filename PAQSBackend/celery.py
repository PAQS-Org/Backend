import os

from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PAQSBackend.settings")

app = Celery("PAQSBackend", broker=settings.CELERY_BROKER_URL)

app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()
@app.task(bind=True, ignore_result=True)
def example_task(self):
    print("You've triggered the example task!")