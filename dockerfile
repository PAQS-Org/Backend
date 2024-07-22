FROM python:3.12.2-slim-bullseye

ENV PYTHONBUFFERED=1


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
    build-essential \
    && apt-get clean

WORKDIR /PAQSBackend

COPY . /PAQSBackend/

RUN pip install -r requirements.txt

CMD gunicorn PAQSBackend.wsgi

