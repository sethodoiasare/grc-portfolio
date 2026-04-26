#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Vuln SLA Tracker — Demo Launcher ==="
echo ""

# Kill any existing servers on our ports
lsof -ti :8003 | xargs kill 2>/dev/null || true
lsof -ti :3000 | xargs kill 2>/dev/null || true
sleep 1

# Seed data
echo "[1/3] Seeding database..."
cd "$DIR" && python3 -m src.seed_data 2>/dev/null

# Start backend
echo "[2/3] Starting backend on :8003..."
cd "$DIR" && python3 -m uvicorn src.api:app --port 8003 --log-level warning &
sleep 2

# Start frontend
echo "[3/3] Starting frontend on :3000..."
cd "$DIR/ui" && npm run dev &
sleep 4

echo ""
echo "=== Ready ==="
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8003"
echo "  Login:    demo@vodafone.com / demo123"
echo ""
echo "Press Ctrl+C to stop all servers."
wait
