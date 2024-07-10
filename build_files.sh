echo "building the proj"
python3.9 -m pip install -r requirements.txt

echo "make migrations"
python3.9 manage.py makemigrations --no-input
python3.9 manage.py migrate --no-input

echo "collecting statics"
python3.9 manage.py collectstatic --no-input --clear