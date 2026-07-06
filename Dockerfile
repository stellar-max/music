# Dockerfile - Works with Docker, Render, VPS

# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads static/css static/js

# Set environment variables
ENV FLASK_DEBUG=False
ENV HOST=0.0.0.0
ENV PORT=5024

# Expose port
EXPOSE 5024

# Start the application
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "-b", "0.0.0.0:5024", "app:app"]
