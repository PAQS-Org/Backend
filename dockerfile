FROM python:3.11-slim-bullseye AS BASE

WORKDIR /app

ENV PIP_DEFAULT_TIMEOUT=100 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-brotli \
    build-essential \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* 

RUN apt install weasyprint

RUN apt install python3-pip \
     libpango-1.0-0 \ 
     libpangoft2-1.0-0 \
      libharfbuzz-subset0

# Set environment variables
ENV LD_LIBRARY_PATH=/usr/lib:/usr/local/lib:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

COPY . /app

RUN  pip install -r requirements.txt --no-cache-dir --compile

RUN apt-get -y purge gcc libc-dev python3-dev

COPY --chown=python:python ./ /app


RUN mkdir -p staticfiles && \
    chown -R python:python staticfiles

# Copy the WSGI entry point
RUN chmod +x /app/deployment/server-entrypoint.sh && \
    chmod +x /app/deployment/worker-entrypoint.sh


EXPOSE 8000
CMD [ "/app/deployment/server-entrypoint.sh" ]
