FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads static/css static/js

ENV FLASK_DEBUG=False
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

CMD ["sh", "-c", "exec gunicorn --worker-class eventlet --workers 1 --bind 0.0.0.0:$PORT --timeout 120 app:app"]
