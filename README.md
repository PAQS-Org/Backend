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

[web-production-ef21.up.railway.app/accounts/company-login/](web-production-ef21.up.railway.app/accounts/company-login/)

Main urls

[web-production-ef21.up.railway.app](web-production-ef21.up.railway.app)

/accounts/
PAQSBackend.urls.py

company-login/
accounts.urls.py

### URLS.py
The urls.py in the accounts.urls.py connects to the CompanyRegistrationView.as_view() in the views.py of the accounts app. The views.py connects to the serializer.py or directly to the models.py.

### VIews.py
A view function, or view for short, is a Python function that takes a web request and returns a web response. This response can be the HTML contents of a web page, or a redirect, or a 404 error, or an XML document, or an image . . . or anything, really. The view itself contains whatever arbitrary logic is necessary to return that response. The code can live anywhere, as long as it’s on the Python path. There’s no other requirement–no “magic,” so to speak.

### Serializers.py
Serializers allow complex data such as querysets and model instances to be converted to native Python datatypes that can then be easily rendered into JSON, XML or other content types. Serializers also provide deserialization, allowing parsed data to be converted back into complex types, after first validating the incoming data.

### Models.py
The models.py contains all the database table and its structure. A model is the single, definitive source of information about the data. It contains the essential fields and behaviors of the data that is being stored. Generally, each model maps to a single database table.

### Admin.py
One of the most powerful parts of Django is the automatic admin interface. It reads metadata from your models to provide a quick, model-centric interface where trusted users can manage content on your site. The admin’s recommended use is limited to an organization’s internal management tool. It’s not intended for building your entire front end around.

## Project Apps

### Accounts
The accounts app has the database table for Company and User. The company is designated for company registration info; whereas the User is designated for all other users. The urls.py exposes the endpoints for registration, login, change of password, and logout for both company and user.

### Social_auth
The social_auth handles User registrations that are done through either of the social media apps such as google, facebook and twitter. For now, only Google is working.

### Payments
The payment app is designated for company payments. This makes use of Paystack. It exposes the endpoint for generating of invoice and payment initialization process. During payment, it receives the product name, the batch number, and the quantity. The price calculation is done and then a request is sent to Paystack to initiate the payment process. When all is done, Paystack sends a post request to the backend. 

### Static
Static is not an app. It only hold static files like images, css and javascript. 

## Creating a superuser 
A superuser account automatically sets a user up as a staff and also gives the user a Superuser status. Its only a superuser that can log into the Django Administration page. As you run the createsuperuser command in the terminal, that account credential can be used to login to the [web-production-ef21.up.railway.app/admin](web-production-ef21.up.railway.app/admin)

# Creating a new service
```commandLine
python manage.py startapp polls
```

Polls is the desired service name. it can be anything. Running the code would create
polls/
    __init__.py
    admin.py
    apps.py
    migrations/
        __init__.py
    models.py
    tests.py
    views.py
    
After that 
1.	register it in the installed app in the settings.py of the PAQSBackend folder.
2.	Register the urls file in the ulrs.py of the PAQSBackend folder. This would look-like 
Path(‘polls/’, include(‘polls.urls’),’
3.	Import the Polls in the model into the admin.py. then register the app in the admin.py. this would look-like admin.site.register(Polls) 
