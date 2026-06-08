# ---- Stage 1: Svelte-Frontend bauen ----
FROM node:20-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci || npm install
COPY frontend/ ./
RUN npm run build   # -> /build/dist

# ---- Stage 2: Python-Runtime (inkl. Node für fantasticon) ----
FROM python:3.12-slim
WORKDIR /app

# System-Dependencies + Node.js für fantasticon (Font-Generierung)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    nodejs \
    npm \
    && npm install -g fantasticon \
    && rm -rf /var/lib/apt/lists/* \
    && npm cache clean --force

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# Gebautes Frontend aus Stage 1 übernehmen
COPY --from=frontend /build/dist ./web

RUN mkdir -p /app/icons /app/temp

EXPOSE 8766

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8766/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8766"]
