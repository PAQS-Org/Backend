# Background

Django is a high-level python web framework that encourages rapid development and clean, pragmatic design. It is mainly an object-relational mapping tool for communicating effectively with a database.

# PAQS Backend

Paqs backend is built with Django to handle the database communication for PAQS project. The project makes use of postgresql database. It is run on railway with the endpoint url: web-production-ef21.up.railway.app

# Installation

```commandLine
pip install requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
python manage.py runserver
```

# Project Structure

In Django, the project is the foundation or parent of the entire project. The main workable file, settings.py includes the database configuration and the application specific settings. The app is the child or mini-services that connects to the project. The urls.py in the project (PAQSBackend) folder is the main entry point. The various apps are connected to it through their url. The url serves as the API endpoint to the various apps

[post-request: ] (Post-request: web-production-ef21.up.railway.app/accounts/company-login/)

```commandLine
conda activate base
```
