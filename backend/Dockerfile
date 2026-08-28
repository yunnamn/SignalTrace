FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg2 and torch/transformers
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# We set PYTHONPATH so that backend and ml_pipeline can be imported
ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
