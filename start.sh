#!/bin/sh
set -e
python manage.py makemigrations
python manage.py makemigrations myaccount review
python manage.py migrate
python manage.py migrate --database=story

ADMIN_USER=${DJANGO_SUPERUSER_USERNAME}
ADMIN_EMAIL=${DJANGO_SUPERUSER_EMAIL}
ADMIN_PASS=${DJANGO_SUPERUSER_PASSWORD}

python manage.py createsuperuser --noinput --username $ADMIN_USER --email $ADMIN_EMAIL || true
echo "from django.contrib.auth import get_user_model; User = get_user_model(); user = User.objects.get(username='$ADMIN_USER'); user.set_password('$ADMIN_PASS'); user.save()" | python manage.py shell

exec python manage.py runserver 0.0.0.0:8000
