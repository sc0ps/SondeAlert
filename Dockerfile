# ---- SondeAlert Dockerfile ----
FROM python:3.11-slim

# Sneller starten, geen pyc bestanden
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Installeer OS-pakketten die nodig zijn voor I²C en numerieke libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    i2c-tools python3-dev build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# Werkmap in de container
WORKDIR /app

# Python-dependencies installeren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App-code kopiëren
COPY src ./src
COPY data ./data

# Zorg dat Python je pakket kan vinden
ENV PYTHONPATH=/app/src

# Start het programma
CMD ["python", "-m", "sondealert.main"]
