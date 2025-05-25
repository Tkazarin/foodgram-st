#!/bin/sh

echo "Waiting for PostgreSQL to become available..."

while ! python -c "import socket; import os; sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM); result = sock.connect_ex(('db', 5432)); sock.close(); exit(result)"; do
  sleep 1
done

echo "PostgreSQL is available, proceeding..."

python manage.py migrate

python manage.py collectstatic --noinput

python manage.py load_data /app/ingredients.json

python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
END

exec "$@"