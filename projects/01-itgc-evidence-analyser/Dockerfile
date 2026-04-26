# ---- Stage 1: Build Next.js frontend ----
FROM node:22-alpine AS ui-builder
WORKDIR /app/ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci
COPY ui/ ./
RUN npm run build

# ---- Stage 2: Final runtime ----
FROM python:3.13-slim

# Install Node.js (for running Next.js production server)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    nginx \
    supervisor \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---- Python backend ----
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
COPY data/ ./data/

# ---- Next.js frontend (built) ----
COPY --from=ui-builder /app/ui/.next/ ./ui/.next/
COPY --from=ui-builder /app/ui/package.json ./ui/
COPY --from=ui-builder /app/ui/node_modules ./ui/node_modules
COPY --from=ui-builder /app/ui/next.config.ts ./ui/
COPY --from=ui-builder /app/ui/public ./ui/public

# ---- Nginx config (reverse proxy: /api → backend, / → frontend) ----
COPY nginx.conf /etc/nginx/sites-available/default
RUN rm /etc/nginx/sites-enabled/default 2>/dev/null; \
    ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/

# ---- Supervisor config ----
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# ---- Startup ----
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 80
CMD ["/start.sh"]
