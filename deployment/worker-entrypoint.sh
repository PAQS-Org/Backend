#!/bin/sh
celery -A PAQSBackend worker --beat -l INFO