#!/bin/bash
set -e

echo "=== Evidence Collection Automator ==="
echo "Initialising database..."
python3 -c "from src.database import init_db, ensure_evidence_store; ensure_evidence_store(); init_db()"

echo "Starting services via supervisord..."
echo "  Backend  → http://0.0.0.0:80/api/"
echo "  Frontend → http://0.0.0.0:80/"
echo "  API Docs → http://0.0.0.0:80/docs"
echo ""

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
