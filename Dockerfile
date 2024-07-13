# Use a minimal Python image for efficiency
FROM python:3.12.3-slim

# Update package lists
RUN apt-get update

# Install dependencies for WeasyPrint
RUN apt-get install -y \
  python3-pip \
  python3-cffi \
  python3-brotli \
  libpango-1.0-0 \
  libpangoft2-1.0-0

# Set working directory
WORKDIR /PAQSBackend

# Install pipenv (assuming it's not already installed in the base image)
RUN pip install pipenv

# Copy Pipfile and Pipfile.lock (ensure they are in the same directory)
COPY Pipfile Pipfile.lock ./

# Install project dependencies using pipenv
RUN pipenv install --deploy --ignore-pipfile

# Copy entire project directory
COPY . .

# Use gunicorn as the main process
CMD ["gunicorn", "PAQSBackend.wsgi"]