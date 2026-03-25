# SEMS+ Scraper — Home Assistant Add-on

> **Disclaimer:**
> This project was generated entirely by AI (GitHub Copilot/Claude). I (Ash) cannot take any accountability for the code, its correctness, or any issues that may arise with SEMS+, GoodWe, or related services. Use at your own risk.

A Home Assistant add-on that scrapes the [GoodWe SEMS+](https://semsplus.goodwe.com) solar portal using a headless Chromium browser and exposes the data via a local HTTP API.

---

## What it does

```
┌──────────────────────────┐
│  SEMS+ Portal (GoodWe)   │
└────────────┬─────────────┘
             │ Playwright (headless Chromium)
┌────────────▼─────────────┐
│  This Add-on (Docker)    │
│  FastAPI on port 8099    │
└────────────┬─────────────┘
             │ HTTP JSON API
┌────────────▼─────────────┐
│  Home Assistant          │
│  REST sensors / HACS     │
└──────────────────────────┘
```

The add-on:

1. Logs in to your SEMS+ account with Playwright
2. Scrapes all available solar metrics from the dashboard
3. Re-scrapes on a configurable interval (default: every 5 minutes)
4. Serves the latest data at `http://<addon>:8099/v1/metrics`

---

## Installation

1. In Home Assistant go to **Settings → Add-ons → Add-on Store**
2. Click the **⋮** menu (top-right) → **Repositories**
3. Paste the repository URL:
   ```
   https://github.com/ashwhall/ha-sems-plus-addon
   ```
4. Click **Add** → close the dialog
5. Find **SEMS+ Scraper** in the store and click **Install**
6. Go to the add-on **Configuration** tab and fill in your credentials
7. **Start** the add-on

---

## Configuration

| Option                  | Type     | Default | Description                          |
| ----------------------- | -------- | ------- | ------------------------------------ |
| `sems_username`         | string   | —       | Your SEMS+ login email               |
| `sems_password`         | password | —       | Your SEMS+ login password            |
| `poll_interval_seconds` | int      | `300`   | Scrape interval in seconds (60–3600) |
| `plant_id`              | string?  | `""`    | Your SEMS+ station ID (see below)    |

All options are set via the Home Assistant UI on the add-on's Configuration tab.

### Finding your Station ID

The `plant_id` is the station UUID used by SEMS+. There are two ways to find it:

**Option A — from the URL bar:**

1. Log in to [semsplus.goodwe.com](https://semsplus.goodwe.com)
2. Navigate to your station/plant dashboard
3. The URL will look like:
   ```
   https://semsplus.goodwe.com/#/station_monitor/station_detail?eyJzdGF0aW9u...
   ```
4. Copy the base64 string after `station_detail?` and decode it (e.g. at [base64decode.org](https://www.base64decode.org) or in a terminal: `echo '<string>' | base64 -d`)
5. The decoded JSON contains your station ID:
   ```json
   {"stationId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", ...}
   ```
6. Copy the `stationId` UUID and paste it into the `plant_id` option

**Option B — from network requests:**

1. Open your browser's **Developer Tools** (F12 or Cmd+Shift+I)
2. Go to the **Network** tab, then navigate to your plant dashboard
3. Look for a `POST` request to a URL like:
   ```
   https://au-gateway.semsportal.com/web/sems/sems-plant/api/portal/stations/basic/info?stationId=<your-station-id>
   ```
4. Copy the `stationId` UUID from the URL

> **Note:** The gateway subdomain may differ by region (e.g. `au-gateway`, `eu-gateway`, `us-gateway`).

---

## API Reference

Once the add-on is running, it exposes two endpoints on port **8099**.

### `GET /v1/metrics`

Returns the latest scraped solar metrics.

```json
{
  "current_power_w": 3450.0,
  "grid_import_w": 0.0,
  "grid_export_w": 1200.0,
  "daily_energy_kwh": 18.7,
  "total_energy_kwh": 12450.3,
  "battery_soc_pct": 85.0,
  "battery_power_w": -500.0,
  "consumption_w": 2250.0,
  "self_consumption_pct": 65.2,
  "timestamp": "2026-03-25T10:30:00Z",
  "plant_id": "abc123",
  "plant_name": "My Solar Plant"
}
```

All fields are **nullable** — a field is `null` if the scraper couldn't find the corresponding value on the dashboard.

Returns **503** if no scrape has completed yet.

### `GET /v1/health`

Returns add-on status.

```json
{
  "status": "ok",
  "version": "0.1.0",
  "last_scrape": "2026-03-25T10:30:00Z",
  "next_scrape": "2026-03-25T10:35:00Z",
  "error": null,
  "scrape_count": 42
}
```

`status` is one of: `ok`, `error`, `starting`.

### OpenAPI docs

Interactive API documentation is available at `http://<addon>:8099/docs`.

---

## Example: Home Assistant REST Sensors

Add this to your `configuration.yaml` to consume the API without the optional HACS integration. This example includes all available sensors as of the latest release:

```yaml
rest:
  - resource: http://localhost:8099/v1/metrics
    scan_interval: 300
    sensor:
      - name: 'Solar Power'
        value_template: '{{ value_json.current_power_w }}'
        unit_of_measurement: 'W'
        device_class: power
        state_class: measurement

      - name: 'Solar Daily Energy'
        value_template: '{{ value_json.daily_generation_kwh }}'
        unit_of_measurement: 'kWh'
        device_class: energy
        state_class: total_increasing

      - name: 'Solar Total Energy'
        value_template: '{{ value_json.total_energy_kwh }}'
        unit_of_measurement: 'kWh'
        device_class: energy
        state_class: total_increasing

      - name: 'Battery SOC'
        value_template: '{{ value_json.battery_soc_pct }}'
        unit_of_measurement: '%'
        device_class: battery
        state_class: measurement

      - name: 'Battery Power'
        value_template: '{{ value_json.battery_power_w }}'
        unit_of_measurement: 'W'
        device_class: power
        state_class: measurement

      - name: 'Grid Export'
        value_template: '{{ value_json.grid_export_w }}'
        unit_of_measurement: 'W'
        device_class: power
        state_class: measurement

      - name: 'Grid Import'
        value_template: '{{ value_json.grid_import_w }}'
        unit_of_measurement: 'W'
        device_class: power
        state_class: measurement

      - name: 'Grid Daily Import'
        value_template: '{{ value_json.daily_import_kwh }}'
        unit_of_measurement: 'kWh'
        device_class: energy
        state_class: total_increasing

      - name: 'Grid Daily Export'
        value_template: '{{ value_json.daily_export_kwh }}'
        unit_of_measurement: 'kWh'
        device_class: energy
        state_class: total_increasing

      - name: 'House Consumption'
        value_template: '{{ value_json.consumption_w }}'
        unit_of_measurement: 'W'
        device_class: power
        state_class: measurement

      - name: 'House Daily Consumption'
        value_template: '{{ value_json.daily_consumption_kwh }}'
        unit_of_measurement: 'kWh'
        device_class: energy
        state_class: total_increasing

      # Uncomment if you want revenue sensors
      # - name: 'Generation Revenue'
      #   value_template: '{{ value_json.generation_revenue }}'
      #   unit_of_measurement: '{{ value_json.revenue_currency }}'
      #   device_class: monetary
      #   state_class: measurement

      # - name: 'Export Revenue'
      #   value_template: '{{ value_json.export_revenue }}'
      #   unit_of_measurement: '{{ value_json.revenue_currency }}'
      #   device_class: monetary
      #   state_class: measurement
```

**Note:** The available fields in the API may change as the SEMS+ dashboard evolves. If you add new sensors, check the `/v1/metrics` endpoint or the OpenAPI docs at `/docs` for the latest field names.

---

## Resource Requirements

| Resource | Minimum        | Notes                              |
| -------- | -------------- | ---------------------------------- |
| RAM      | ~512 MB        | Chromium is the main consumer      |
| CPU      | Minimal        | Spikes briefly during each scrape  |
| Disk     | ~300 MB        | Chromium binaries + Python deps    |
| Arch     | amd64, aarch64 | armv7 (RPi 3) is **not supported** |

---

## Security

- **Credentials** are stored in Home Assistant's add-on options (`/data/options.json`) — never logged or exposed via the API.
- **Session cookies** are persisted to `/data/cookies.json` — accessible only inside the add-on container.
- The HTTP API has **no authentication** and is intended for use on your local network only. **Do not expose port 8099 to the internet.**
- No sensitive data appears in log output.

---

## Development

### Project structure

```
repository.yaml                  # HA add-on repository metadata
sems_plus_scraper/
├── config.yaml                  # Add-on manifest (name, version, options)
├── build.yaml                   # Multi-arch base image mapping
├── Dockerfile                   # Python 3.12 + Chromium + FastAPI
├── run.sh                       # Entrypoint — launches uvicorn
├── DOCS.md                      # Documentation shown in HA UI
├── CHANGELOG.md
└── src/
    ├── __init__.py
    ├── config.py                # Reads /data/options.json
    ├── models.py                # Pydantic response schemas
    ├── scraper.py               # Playwright login + scrape logic
    └── main.py                  # FastAPI app + background scheduler
```

### CSS selectors

The scraper uses placeholder selectors (prefixed `TODO_`). To make the scraper functional, you need to provide the real CSS selectors for the SEMS+ dashboard elements. See `src/scraper.py` for the full list of placeholders.

---

## Roadmap

- [ ] Real CSS selectors for semsplus.goodwe.com
- [ ] Companion HACS integration (`ha-sems-plus-integration`) for native HA entities + UI config flow
- [ ] Ingress support (proxy API through HA UI — no exposed port)
- [ ] Multi-plant support
- [ ] Historical data endpoint

---

## License

MIT — see [LICENSE](LICENSE).
