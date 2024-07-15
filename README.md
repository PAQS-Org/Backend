# PAQS Backend

## Run Locally

```commandLine
mv .env .env.production
cp .env.local .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
Make sure you do not commit .env, .env.production or .env.local

## Commands

```commandLine
make migrations
python manage.py
manage.py migrate
run server
```

## Using Conda

```commandLine
conda activate base
```
