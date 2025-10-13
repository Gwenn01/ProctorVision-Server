# ---- Base Image ----
FROM python:3.10-slim

# Prevent Python buffering logs
ENV PYTHONUNBUFFERED=1

# Install system-level dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Upgrade pip + install deps
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Expose Flask default port
EXPOSE 5000

# Run your app
CMD ["python", "app.py"]
