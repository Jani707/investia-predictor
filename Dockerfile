# Use Python 3.9 slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage cache
COPY backend/requirements.txt .

# Install Python dependencies
# Upgrade pip first
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m textblob.download_corpora

# Copy the rest of the application
COPY . .

# Create a directory for cache/data and set permissions
# Hugging Face Spaces runs as user 1000 by default
RUN mkdir -p backend/data backend/saved_models
RUN chmod -R 777 backend/data backend/saved_models

# Expose port 7860 (Hugging Face default)
EXPOSE 7860

# Start the application
# Note: We point to backend.app.main:app and set the port to 7860
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
