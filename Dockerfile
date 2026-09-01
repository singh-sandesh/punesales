# syntax=docker/dockerfile:1.6

# =========================================================
# Stage 1 - build the React frontend with yarn
# =========================================================
FROM node:20-alpine AS frontend
WORKDIR /frontend

# Install deps first (better layer caching)
COPY frontend/package.json frontend/yarn.lock* ./
RUN corepack enable && yarn install --frozen-lockfile --network-timeout 600000 || \
    yarn install --network-timeout 600000

# Copy source and build
COPY frontend/ ./
# Same-origin: frontend talks to /api on the same host as the backend serves it
ENV REACT_APP_BACKEND_URL=""
RUN yarn build

# =========================================================
# Stage 2 - Python backend that also serves the React build
# =========================================================
FROM python:3.11-slim AS runtime
WORKDIR /app

# System deps kept minimal
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r backend/requirements.txt

# Backend code
COPY backend/ ./backend/

# React build produced by stage 1
COPY --from=frontend /frontend/build ./frontend/build

# server.py looks here by default (ROOT_DIR.parent / 'frontend' / 'build')
ENV FRONTEND_BUILD_DIR=/app/frontend/build
ENV PYTHONUNBUFFERED=1
ENV SEED_DEMO_DATA=false

# Railway injects $PORT
ENV PORT=8000
EXPOSE 8000

WORKDIR /app/backend
CMD ["sh", "-c", "python -m uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
