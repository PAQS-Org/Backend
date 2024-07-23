FROM ubuntu:22.04-slim AS builder

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-cffi \
    python3-brotli \
    libpango1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    libffi-dev \
    libcairo2 \
    libpango1.0-dev \
    libjpeg62-turbo-dev \
    libgdk-pixbuf2.0-0 \
    libgdk-pixbuf2.0-dev \
    weasyprint \
    build-essential \
    libgobject-2.0-0 \
    && apt-get clean

RUN dpkg -l | grep -E "libpango|libcairo|libgdk-pixbuf"

# Identify Python version (adjust based on your actual version)
RUN python3 --version | cut -d ' ' -f 2 | cut -d '.' -f 1,2 | tr -d '\n'  PYTHON_VERSION=



FROM python:3.12.2-slim-bullseye

RUN cp -r /usr/local/lib/python${PYTHON_VERSION}/dist-packages/* /app/lib

ENV PYTHONBUFFERED=1

WORKDIR /PAQSBackend

COPY . /PAQSBackend/

RUN pip install -r requirements.txt

COPY PAQSBackend.wsgi /PAQSBackend/PAQSBackend.wsgi

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "PAQSBackend.wsgi"]

