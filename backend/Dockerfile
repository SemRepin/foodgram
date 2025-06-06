FROM python:3.9

WORKDIR /app

RUN mkdir -p /data

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY ../data/ /data/

RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "foodgram.wsgi:application"] 