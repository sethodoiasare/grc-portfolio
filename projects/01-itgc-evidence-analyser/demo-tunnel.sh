#!/bin/bash
# =============================================================================
# ITGC Evidence Analyser — Demo Tunnel Launcher
# Run this any time you want to demo the app to someone.
# It starts the backend, frontend, and a public tunnel.
# Press Ctrl+C when done — everything stops.
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
sleep 1

# Start backend
echo "[1/3] Starting backend on port 8001..."
cd "$PROJECT_DIR"
python3 -m uvicorn src.api:app --port 8001 &
BACKEND_PID=$!

# Start frontend
echo "[2/3] Starting frontend on port 3000..."
cd "$PROJECT_DIR/ui"
npm run dev -- --port 3000 &
FRONTEND_PID=$!

# Wait for servers to be ready
echo "Waiting for servers..."
for i in {1..30}; do
  if curl -s http://localhost:8001/api/v1/health > /dev/null 2>&1 && curl -s http://localhost:3000 > /dev/null 2>&1; then
    break
  fi
  sleep 1
done

# Start tunnel
echo "[3/3] Starting public tunnel..."
echo ""
echo "============================================"
echo " DEMO URL: (will appear below)"
echo " Share this link — accessible from any device"
echo " Press Ctrl+C to stop"
echo "============================================"
echo ""

# Trap Ctrl+C to clean up
cleanup() {
  echo ""
  echo "Shutting down..."
  kill $BACKEND_PID 2>/dev/null || true
  kill $FRONTEND_PID 2>/dev/null || true
  echo "Demo stopped."
  exit 0
}
trap cleanup INT TERM

# Run tunnel — this blocks until Ctrl+C
cloudflared tunnel --url http://localhost:3000 2>&1
