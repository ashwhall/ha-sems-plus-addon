#!/usr/bin/env bash
# shellcheck shell=bash

set -euo pipefail

echo "[INFO] Starting SEMS+ Scraper add-on..."

cd /app

# exec replaces this shell so S6 can manage the process directly
exec python3 -m uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8099 \
    --log-level info
