FROM python:3.11-slim-bullseye

WORKDIR /app

ENV PIP_DEFAULT_TIMEOUT=100 \
    # Allow statements and log messages to immediately appear
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # disable a pip version check to reduce run-time & log-spam
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # cache is useless in docker image, so disable it to reduce image size
    PIP_NO_CACHE_DIR=1
# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-brotli \
    build-essential \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* 

RUN apt install weasyprint

# Set environment variables
ENV LD_LIBRARY_PATH=/usr/lib:/usr/local/lib:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# Set the working directory

# Copy the application code
COPY . /app

# Install Python dependencies
RUN  pip install -r requirements.txt --no-cache-dir --compile

RUN apt-get -y purge gcc libc-dev python3-dev

# Add all application code from this folder, including deployment entrypoints
COPY --chown=python:python ./ /app


# Create staticfiles folder
RUN mkdir -p staticfiles && \
    chown -R python:python staticfiles

# Copy the WSGI entry point
RUN chmod +x /app/deployment/server-entrypoint.sh && \
    chmod +x /app/deployment/worker-entrypoint.sh

# Command to run the application
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "PAQSBackend.wsgi"]

EXPOSE 8000
CMD [ "/app/deployment/server-entrypoint.sh" ]
