# Use official Python runtime as base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY database.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port (Cloud Run will set the PORT env variable)
EXPOSE 8080

# Run the application
CMD ["python", "app.py"]
