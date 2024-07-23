FROM python:3.12.2-slim-bullseye

# Install system dependencies
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
    libjpeg62-turbo-dev \
    libgdk-pixbuf2.0-0 \
    libgdk-pixbuf2.0-dev \
    libgobject-2.0-0 \
    libgobject2.0-dev \
    build-essential \
    && apt-get clean

# Set environment variables
ENV LD_LIBRARY_PATH=/usr/lib:/usr/local/lib:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# Set the working directory
WORKDIR /PAQSBackend

# Copy the application code
COPY . /PAQSBackend/

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy the WSGI entry point
COPY PAQSBackend.wsgi /PAQSBackend/PAQSBackend.wsgi

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "PAQSBackend.wsgi"]
