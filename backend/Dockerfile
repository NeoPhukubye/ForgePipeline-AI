FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl docker.io \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
COPY requirements.txt /app/agent-requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r agent-requirements.txt

# Copy agent layer
COPY forgepipeline_ai /app/forgepipeline_ai

# Copy backend
COPY backend/app /app/app

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
