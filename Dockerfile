# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install required system dependencies for WeasyPrint
RUN apt-get update && apt-get install -y \
    libpango1.0-dev \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libgobject-2.0-0 \
    libpango-1.0-0 \
    && apt-get clean

# Set the working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Run Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
