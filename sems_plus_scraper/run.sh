#!/usr/bin/env bash
# shellcheck shell=bash

set -euo pipefail

# Log using bashio if available (HA add-on), otherwise plain echo
if command -v bashio &>/dev/null; then
    bashio::log.info "Starting SEMS+ Scraper add-on..."
else
    echo "[INFO] Starting SEMS+ Scraper..."
fi

cd /app

# exec replaces this shell so S6 can manage the process directly
exec python3 -m uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8099 \
    --log-level info
