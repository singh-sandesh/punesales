# syntax=docker/dockerfile:1.6

# =========================================================
# Stage 1 - build the React frontend
# =========================================================
FROM node:20-bookworm-slim AS frontend
WORKDIR /frontend

# yarn ships with node:20 images; just make sure it's callable
RUN yarn --version

# Install deps (no frozen-lockfile - the lockfile drifts easily on React 19)
COPY frontend/package.json frontend/yarn.lock* ./
RUN yarn install --network-timeout 600000

# Copy source and build
COPY frontend/ ./
# Same-origin: React talks to /api on the same host that serves it
ENV REACT_APP_BACKEND_URL=""
# CRA on Node 20 needs this flag; also silence CI treating warnings as errors
ENV NODE_OPTIONS=--openssl-legacy-provider
ENV CI=false
RUN yarn build

# =========================================================
# Stage 2 - Python backend that also serves the React build
# =========================================================
FROM python:3.11-slim AS runtime
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
COPY --from=frontend /frontend/build ./frontend/build

ENV FRONTEND_BUILD_DIR=/app/frontend/build
ENV PYTHONUNBUFFERED=1
ENV SEED_DEMO_DATA=false
ENV PORT=8000
EXPOSE 8000

WORKDIR /app/backend
CMD ["sh", "-c", "python -m uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
