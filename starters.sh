#!/bin/bash
gunicorn PAQSBackend.wsgi
celery -A your_app_name worker --pool=solo -l info