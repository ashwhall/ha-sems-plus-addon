"""FastAPI application — HTTP API + background scrape scheduler."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .config import AddonConfig, load_config
from .models import HealthResponse, PlantMetrics
from .scraper import SEMSScraper

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application state (module-level singletons, set during lifespan)
# ---------------------------------------------------------------------------
_config: Optional[AddonConfig] = None
_scraper: Optional[SEMSScraper] = None
_latest_metrics: Optional[PlantMetrics] = None
_last_error: Optional[str] = None
_last_scrape: Optional[datetime] = None
_next_scrape: Optional[datetime] = None
_scrape_count: int = 0
_scrape_task: Optional[asyncio.Task] = None


# ---------------------------------------------------------------------------
# Background scheduler
# ---------------------------------------------------------------------------

async def _scrape_loop() -> None:
    """Periodically scrape SEMS+ and store the latest metrics."""
    global _latest_metrics, _last_error, _last_scrape, _next_scrape, _scrape_count

    if not _config or not _scraper:
        return

    while True:
        _next_scrape = datetime.now(
            timezone.utc) + timedelta(seconds=_config.poll_interval_seconds)
        try:
            logger.info("Starting scrape...")
            _latest_metrics = await _scraper.scrape_metrics()
            _last_scrape = datetime.now(timezone.utc)
            _last_error = None
            _scrape_count += 1
            logger.info("Scrape #%d succeeded", _scrape_count)
        except Exception as exc:
            _last_error = str(exc)
            logger.exception("Scrape failed: %s", exc)

        await asyncio.sleep(_config.poll_interval_seconds)


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start browser + scheduler on startup, clean up on shutdown."""
    global _config, _scraper, _scrape_task

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("SEMS+ Scraper starting up...")

    _config = load_config()
    _scraper = SEMSScraper(_config)
    _scrape_task = asyncio.create_task(_scrape_loop())

    yield  # app is running

    logger.info("Shutting down...")
    if _scrape_task:
        _scrape_task.cancel()
        try:
            await _scrape_task
        except asyncio.CancelledError:
            pass
    # No browser to close; scraper is now stateless


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="SEMS+ Scraper",
    version="0.1.0",
    docs_url="/docs",
    lifespan=lifespan,
)



@app.get("/v1/metrics", response_model=PlantMetrics)
async def get_metrics():
    """Return the latest scraped plant metrics, ensuring no string 'None' values. Logs extra info if metrics are missing or stale."""
    if _latest_metrics is None:
        logger.warning("/v1/metrics requested but no metrics are cached yet (first scrape may still be running)")
        return JSONResponse(
            status_code=503,
            content={
                "detail": "No metrics available yet — first scrape may still be running."},
        )
    # Defensive: Only return last good metrics, never zeros unless missing in last scrape
    metrics_dict = _latest_metrics.model_dump()
    numeric_fields = [
        'current_power_w', 'grid_import_w', 'grid_export_w',
        'daily_generation_kwh', 'daily_export_kwh', 'daily_import_kwh', 'daily_consumption_kwh',
        'generation_revenue', 'export_revenue', 'total_energy_kwh',
        'battery_soc_pct', 'battery_power_w', 'consumption_w'
    ]
    missing = []
    for k in numeric_fields:
        v = metrics_dict.get(k, None)
        if v is None or v == "None":
            metrics_dict[k] = 0
            missing.append(k)
    if missing:
        logger.warning("/v1/metrics: Returning cached metrics, but the following fields are missing or None: %s", ', '.join(missing))
    # Optionally, warn if data is stale (older than 2x poll interval)
    if _last_scrape and _config:
        age = (datetime.now(timezone.utc) - _last_scrape).total_seconds()
        if age > 2 * _config.poll_interval_seconds:
            logger.warning("/v1/metrics: Returning stale metrics (last scrape was %.0f seconds ago)", age)
    return PlantMetrics(**metrics_dict)


@app.get("/v1/health", response_model=HealthResponse)
async def get_health():
    """Return add-on health and status."""
    if _last_scrape is None and _last_error is None:
        status = "starting"
    elif _last_error:
        status = "error"
    else:
        status = "ok"

    return HealthResponse(
        status=status,
        version="0.1.0",
        last_scrape=_last_scrape,
        next_scrape=_next_scrape,
        error=_last_error,
        scrape_count=_scrape_count,
    )
