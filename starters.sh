#!/bin/bash
gunicorn PAQSBackend.wsgi
celery -A PAQSBackend worker -l info