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
    libcairo2-dev \
    libpango1.0-dev \
    libjpeg62-turbo-dev \
    libgdk-pixbuf2.0-0 \
    libgdk-pixbuf2.0-dev \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    && apt-get clean

RUN dpkg -l | grep -E "libpango|libcairo|libgdk-pixbuf"


FROM python:3.12.2-slim-bullseye

ENV PYTHONBUFFERED=1

WORKDIR /PAQSBackend

COPY . /PAQSBackend/

RUN pip install -r requirements.txt

COPY PAQSBackend.wsgi /PAQSBackend/PAQSBackend.wsgi

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "PAQSBackend.wsgi"]

