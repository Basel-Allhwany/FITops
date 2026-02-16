# FitOps Timer - Production Dockerfile
FROM python:3.12-slim

# Labels
LABEL maintainer="FitOps Team"
LABEL version="1.0.0"
LABEL description="FitOps Timer - Focus & Exercise App"

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=false

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY data/exercises.csv ./data/exercises.csv

# Create data directory
RUN mkdir -p ./data

# Expose port
EXPOSE 5000

# Run with Gunicorn
WORKDIR /app/backend
CMD ["gunicorn", "--config", "gunicorn.conf.py", "main:app"]
