#!/bin/bash
# =============================================================================
# ITGC Evidence Analyser — Demo Tunnel Launcher
# Starts backend + frontend + nginx reverse proxy, then creates a public
# Cloudflare Tunnel. Single URL, no CORS issues, multipart uploads work.
# Run this, share the URL, Ctrl+C when done.
# =============================================================================
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "============================================"
echo " ITGC Evidence Analyser — Demo Mode"
echo "============================================"
echo ""

# Kill anything already on these ports
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8080 | xargs kill -9 2>/dev/null || true
pkill -f cloudflared 2>/dev/null || true
sleep 1

# Start backend
echo "[1/4] Starting backend on port 8001..."
cd "$PROJECT_DIR"
python3 -m uvicorn src.api:app --port 8001 &
BACKEND_PID=$!

# Build and start frontend
echo "[2/4] Building frontend..."
cd "$PROJECT_DIR/ui"
npm run build 2>&1 | tail -1
echo "Starting frontend on port 3000..."
npm start -- --port 3000 &
FRONTEND_PID=$!

# Start nginx on port 8080 (avoid conflict with system nginx)
echo "[3/4] Starting local nginx on port 8080..."
cd "$PROJECT_DIR"
cat > /tmp/itgc-demo-nginx.conf << 'NGINX'
worker_processes 1;
error_log /tmp/itgc-nginx-error.log;
pid /tmp/itgc-nginx.pid;

events { worker_connections 64; }

http {
    access_log off;
    client_max_body_size 50M;

    server {
        listen 8080;

        location / {
            proxy_pass http://127.0.0.1:3000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_read_timeout 300s;
        }

        location /api/ {
            proxy_pass http://127.0.0.1:8001;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_read_timeout 300s;
        }

        location /docs { proxy_pass http://127.0.0.1:8001; }
        location /openapi.json { proxy_pass http://127.0.0.1:8001; }
    }
}
NGINX
nginx -c /tmp/itgc-demo-nginx.conf &
NGINX_PID=$!

# Wait for servers to be ready
echo "Waiting for servers..."
for i in {1..30}; do
  if curl -s http://localhost:8001/api/v1/health > /dev/null 2>&1 && curl -s http://localhost:3000 > /dev/null 2>&1; then
    break
  fi
  sleep 1
done

# Start tunnel
echo "[4/4] Starting public tunnel..."
echo ""
echo "============================================"
echo " DEMO URL: (will appear below)"
echo " Share this link — accessible from any device"
echo " Press Ctrl+C to stop"
echo "============================================"
echo ""

cleanup() {
  echo ""
  echo "Shutting down..."
  kill $BACKEND_PID 2>/dev/null || true
  kill $FRONTEND_PID 2>/dev/null || true
  kill $NGINX_PID 2>/dev/null || true
  pkill -f cloudflared 2>/dev/null || true
  rm -f /tmp/itgc-demo-nginx.conf /tmp/itgc-nginx-error.log /tmp/itgc-nginx.pid
  echo "Demo stopped."
  exit 0
}
trap cleanup INT TERM

cloudflared tunnel --url http://localhost:8080 2>&1
