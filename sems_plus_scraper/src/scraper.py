"""Playwright-based scraper for the GoodWe SEMS+ portal."""

from __future__ import annotations

import base64
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import os
import shutil

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from .config import AddonConfig
from .models import PlantMetrics

logger = logging.getLogger(__name__)

SEMS_URL = "https://semsplus.goodwe.com"
_DOCKER_COOKIE_PATH = Path("/data/cookies.json")
_LOCAL_COOKIE_PATH = Path(__file__).parent.parent / "cookies.json"
COOKIE_PATH = _DOCKER_COOKIE_PATH if _DOCKER_COOKIE_PATH.parent.exists(
) else _LOCAL_COOKIE_PATH


class SEMSScraper:
    """Headless Chromium scraper for semsplus.goodwe.com."""

    def __init__(self, config: AddonConfig) -> None:
        self._config = config

    # No persistent browser state or lifecycle methods needed

    # ------------------------------------------------------------------
    # Cookie persistence
    # ------------------------------------------------------------------

    async def _save_cookies(self, context: BrowserContext) -> None:
        """Persist session cookies to /data/ for reuse across restarts."""
        cookies = await context.cookies()
        COOKIE_PATH.write_text(
            json.dumps(cookies, default=str),
            encoding="utf-8",
        )
        logger.debug("Saved %d cookies", len(cookies))

    async def _restore_cookies(self, context: BrowserContext) -> None:
        """Load previously saved cookies into the browser context."""
        if not COOKIE_PATH.exists():
            return
        try:
            cookies = json.loads(COOKIE_PATH.read_text(encoding="utf-8"))
            await context.add_cookies(cookies)
            logger.debug("Restored %d cookies", len(cookies))
        except (json.JSONDecodeError, KeyError):
            logger.warning("Could not restore cookies — will re-login")
            COOKIE_PATH.unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def login(self, page: Page, context: BrowserContext) -> None:
        """Authenticate against the SEMS+ portal."""
        logger.info("Logging in to SEMS+...")
        await page.goto(f"{SEMS_URL}/#/login", wait_until="networkidle", timeout=60_000)

        # Dismiss cookie consent banner if present
        try:
            cookie_btn = page.locator(
                "div.index-module_btns_815c4 button.ant-btn-primary")
            if await cookie_btn.count() > 0:
                await cookie_btn.click(timeout=5_000)
                logger.info("Dismissed cookie consent banner")
                await page.wait_for_timeout(500)
        except Exception:
            logger.debug("No cookie banner to dismiss")

        # Fill email
        await page.fill("input#account", self._config.sems_username)

        # Fill password
        await page.fill("input#pwd", self._config.sems_password)

        # Accept login terms checkbox (click the wrapper label, not the hidden input)
        checkbox_wrapper = page.locator(
            "div.index-module_loginFooter_ebd64 .ant-checkbox-wrapper")
        await checkbox_wrapper.click()

        # Click login button
        await page.click("button.index-module_loginBtn_c350a")

        # Wait for navigation away from the login page
        await page.wait_for_url(f"{SEMS_URL}/**", timeout=30_000)
        await self._save_cookies(context)
        logger.info("Login successful")

    # ------------------------------------------------------------------
    # Scrape
    # ------------------------------------------------------------------

    async def scrape_metrics(self) -> PlantMetrics:
        """Stateless: launch browser, scrape, close browser, return metrics."""
        async with async_playwright() as p:
            # In Docker, use the system Chromium; locally, let Playwright find its own
            chromium_path = os.environ.get(
                "CHROMIUM_EXECUTABLE", "/usr/bin/chromium-browser")
            launch_kwargs: dict = {
                "headless": True,
                "args": [
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--disable-setuid-sandbox",
                ],
            }
            if shutil.which(chromium_path):
                launch_kwargs["executable_path"] = chromium_path

            browser = await p.chromium.launch(**launch_kwargs)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            await self._restore_cookies(context)
            page = await context.new_page()

            # Check if cookies are valid by loading dashboard, else login
            dashboard_url = SEMS_URL
            if self._config.plant_id:
                payload = json.dumps(
                    {"stationId": self._config.plant_id}, separators=(",", ":"))
                encoded = base64.b64encode(payload.encode()).decode()
                dashboard_url = f"{SEMS_URL}/#/station_monitor/station_detail?{encoded}"

            await page.goto(dashboard_url, wait_until="networkidle", timeout=60_000)
            # If redirected to login, perform login
            if "login" in page.url:
                await self.login(page, context)
                await page.goto(dashboard_url, wait_until="networkidle", timeout=60_000)

            # Allow dynamic content to render (increase to 8 seconds)
            await page.wait_for_timeout(8000)

            # Selectors: each metric block is a .index-module_textRich_503fd container
            # with a label in .index-module_textLabelName_23179[title="<Label>"].
            # The value is in .index-module_textValue_25038.
            # Battery SOC is a separate span .index-module_socValue_10fdd inside the value div.
            _block = "div.index-module_textRich_503fd"
            _label = "div.index-module_textLabelName_23179"
            _value = "div.index-module_textValue_25038"
            _soc = "span.index-module_socValue_10fdd"

            def _sel(label: str) -> str:
                return f"{_block}:has({_label}[title='{label}']) {_value}"

            grid_power = await self._read_metric(page, _sel("Grid"))
            solar_power = await self._read_metric(page, _sel("Solar"))
            load_power = await self._read_metric(page, _sel("Load"))
            battery_power = await self._read_metric_direct_text(page, f"{_block}:has({_label}[title='Battery']) {_value}")
            battery_soc = await self._read_metric(page, f"{_block}:has({_label}[title='Battery']) {_soc}")

            if any(x is None for x in [solar_power, grid_power, load_power]):
                html = await page.content()
                logger.warning(
                    "One or more main metrics missing. Dashboard HTML follows.\n%s", html)

            _daily_block = "div.index-module_inComeLeft_41e28"
            _daily_title = "div.index-module_title_6dff4"
            _daily_num = "span.index-module_num_989cb"
            _daily_unit = "span.index-module_unit_da158"

            def _daily_sel(title: str) -> str:
                return f"{_daily_block}:has({_daily_title}:has-text('{title}')) {_daily_num}"

            daily_generation = await self._read_metric(page, _daily_sel("Energy Generation"))
            generation_revenue = await self._read_metric(page, _daily_sel("Generation Revenue"))
            daily_export = await self._read_metric(page, _daily_sel("Grid Export Energy"))
            export_revenue = await self._read_metric(page, _daily_sel("To-Grid Revenue"))
            daily_import = await self._read_metric(page, _daily_sel("Import Energy"))
            daily_consumption = await self._read_metric(page, _daily_sel("Energy Consumption"))

            revenue_currency = await self._read_revenue_currency(page, f"{_daily_block}:has({_daily_title}:has-text('Generation Revenue')) {_daily_unit}")

            metrics = PlantMetrics(
                current_power_w=solar_power,
                grid_import_w=grid_power,
                consumption_w=load_power,
                battery_power_w=battery_power,
                battery_soc_pct=battery_soc,
                daily_generation_kwh=daily_generation,
                daily_export_kwh=daily_export,
                daily_import_kwh=daily_import,
                daily_consumption_kwh=daily_consumption,
                generation_revenue=generation_revenue,
                export_revenue=export_revenue,
                revenue_currency=revenue_currency,
                timestamp=datetime.now(timezone.utc),
                plant_id=self._config.plant_id or None,
            )

            logger.info(
                "Scrape complete: solar=%s W, grid=%s W, load=%s W, "
                "battery=%s W (%s%%), daily_gen=%s kWh, daily_import=%s kWh",
                metrics.current_power_w,
                metrics.grid_import_w,
                metrics.consumption_w,
                metrics.battery_power_w,
                metrics.battery_soc_pct,
                metrics.daily_generation_kwh,
                metrics.daily_import_kwh,
            )
            await context.close()
            await browser.close()
            return metrics

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _read_metric_direct_text(self, page: Page, selector: str) -> Optional[float]:
        """Read only the direct text node of an element, ignoring children (e.g. SOC span)."""
        try:
            element = page.locator(selector).first
            if await element.count() == 0:
                return None
            text = await element.evaluate(
                "el => Array.from(el.childNodes).filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim()"
            )
            if not text:
                return None
            cleaned = text.replace(",", "").strip()
            for suffix in ("w", "kw", "kwh", "mwh", "%", "wh"):
                cleaned = cleaned.lower().removesuffix(suffix).strip()
            return float(cleaned)
        except (ValueError, Exception) as exc:
            logger.debug(
                "Could not read direct text from '%s': %s", selector, exc)
            return None

    async def _read_metric(self, page: Page, selector: str) -> Optional[float]:
        """Try to read a numeric value from a DOM element."""
        text = await self._read_text(page, selector)
        if text is None:
            return None
        cleaned = text.replace(",", "").strip()
        for suffix in ("w", "kw", "kwh", "mwh", "%", "wh"):
            cleaned = cleaned.lower().removesuffix(suffix).strip()
        try:
            return float(cleaned)
        except ValueError:
            logger.debug(
                "Could not parse '%s' as float from selector '%s'", text, selector)
            return None

    async def _read_revenue_currency(self, page: Page, selector: str) -> Optional[str]:
        """Extract currency code from a unit span like ' AUD (A$)'."""
        text = await self._read_text(page, selector)
        if not text:
            return None
        cleaned = text.strip()
        token = cleaned.split("(")[0].strip().split()[0] if cleaned else None
        return token

    async def _read_text(self, page: Page, selector: str) -> Optional[str]:
        """Try to read inner text from a DOM element."""
        try:
            element = page.locator(selector).first
            if await element.count() == 0:
                return None
            return (await element.inner_text()).strip()
        except Exception:
            logger.debug("Could not read text from selector '%s'", selector)
            return None
