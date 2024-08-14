#!/bin/sh
celery -A PAQSBackend worker --beat --concurrency -l INFO