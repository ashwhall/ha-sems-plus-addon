"""Pydantic models for API responses."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PlantMetrics(BaseModel):
    """All available metrics scraped from the SEMS+ dashboard."""

    # Power (instantaneous)
    current_power_w: Optional[float] = Field(None, description="Current output power in watts")
    grid_import_w: Optional[float] = Field(None, description="Power drawn from grid in watts")
    grid_export_w: Optional[float] = Field(None, description="Power exported to grid in watts")

    # Energy (daily totals)
    daily_generation_kwh: Optional[float] = Field(None, description="Energy generated today in kWh")
    daily_export_kwh: Optional[float] = Field(None, description="Energy exported to grid today in kWh")
    daily_import_kwh: Optional[float] = Field(None, description="Energy imported from grid today in kWh")
    daily_consumption_kwh: Optional[float] = Field(None, description="Total energy consumed today in kWh")

    # Revenue (daily)
    generation_revenue: Optional[float] = Field(None, description="Generation revenue today (local currency)")
    export_revenue: Optional[float] = Field(None, description="Grid export revenue today (local currency)")
    revenue_currency: Optional[str] = Field(None, description="Revenue currency code, e.g. AUD")

    # Energy (lifetime)
    total_energy_kwh: Optional[float] = Field(None, description="Lifetime energy generated in kWh")

    # Battery
    battery_soc_pct: Optional[float] = Field(None, description="Battery state of charge in percent")
    battery_power_w: Optional[float] = Field(None, description="Battery charge/discharge power in watts (positive=charging)")

    # Consumption
    consumption_w: Optional[float] = Field(None, description="Current household consumption in watts")

    # Metadata
    timestamp: Optional[datetime] = Field(None, description="When the metrics were scraped")
    plant_id: Optional[str] = Field(None, description="SEMS+ plant identifier")
    plant_name: Optional[str] = Field(None, description="SEMS+ plant display name")


class HealthResponse(BaseModel):
    """Add-on health and status."""

    status: str = Field(..., description="ok | error | starting")
    version: str = Field("0.1.0", description="Add-on version")
    last_scrape: Optional[datetime] = Field(None, description="Timestamp of last successful scrape")
    next_scrape: Optional[datetime] = Field(None, description="Estimated next scrape time")
    error: Optional[str] = Field(None, description="Last error message, if any")
    scrape_count: int = Field(0, description="Total successful scrapes since startup")
