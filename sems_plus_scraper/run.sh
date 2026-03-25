#!/usr/bin/env bash
# shellcheck shell=bash

set -euo pipefail

# Graceful shutdown
trap 'kill -TERM $PID 2>/dev/null; wait $PID' SIGTERM SIGINT

# Log using bashio if available (HA add-on), otherwise plain echo
if command -v bashio &>/dev/null; then
    bashio::log.info "Starting SEMS+ Scraper add-on..."
else
    echo "[INFO] Starting SEMS+ Scraper..."
fi

# Launch the FastAPI server
python3 -m uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8099 \
    --log-level info &

PID=$!
wait $PID
