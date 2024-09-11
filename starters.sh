#!/bin/bash
gunicorn PAQSBackend.wsgi
celery -A PAQSBackend worker --pool=solo -l info