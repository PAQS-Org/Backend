FROM python:3.12.2-slim-bullseye

ENV PYTHONBUFFERED=1


RUN apt-get update && apt-get -y install python3-pip python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0

WORKDIR /PAQSBackend

COPY . /PAQSBackend/

RUN pip install -r requirements.txt

CMD gunicorn PAQSBackend.wsgi

