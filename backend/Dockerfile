FROM python:3.11-slim

WORKDIR /app

# System deps kept minimal
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8001/api/bootstrap || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
