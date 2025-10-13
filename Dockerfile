# ---- Dockerfile ----
FROM python:3.10-slim

# Prevent Python buffering & caching
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ✅ Install only the correct OpenCV system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first (for build cache efficiency)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy rest of app
COPY . .

EXPOSE 5000
CMD ["python", "app.py"]
