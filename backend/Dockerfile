FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/all_static && \
    mkdir -p /app/media && \
    chmod -R 777 /app/media && \
    chmod -R 777 /app/all_static

COPY . .

RUN chmod +x /app/start.sh

ENTRYPOINT ["/app/start.sh"]

CMD ["gunicorn", "-b", "0.0.0.0:8000", "foodgram_back.wsgi"]