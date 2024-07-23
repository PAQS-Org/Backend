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


FROM python:3.12.2-slim-bullseye

COPY --from=builder /usr/lib /usr/lib
COPY --from=builder /usr/bin /usr/bin
COPY --from=builder /usr/include /usr/include
COPY --from=builder /usr/share /usr/share

ENV PYTHONBUFFERED=1

WORKDIR /PAQSBackend

COPY . /PAQSBackend/

RUN pip install -r requirements.txt

COPY PAQSBackend.wsgi /PAQSBackend/PAQSBackend.wsgi

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "PAQSBackend.wsgi"]

