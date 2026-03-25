# SEMS+ Scraper

Scrapes the GoodWe SEMS+ solar portal and exposes metrics via a local HTTP API.

## Configuration

| Option                  | Type     | Default | Description                              |
| ----------------------- | -------- | ------- | ---------------------------------------- |
| `sems_username`         | string   | —       | Your SEMS+ login email                   |
| `sems_password`         | password | —       | Your SEMS+ login password                |
| `poll_interval_seconds` | int      | `300`   | Scrape interval in seconds (60–3600)     |
| `plant_id`              | string?  | `""`    | Optional — target a specific plant by ID |

## Usage

Once the add-on is started, it scrapes SEMS+ on the configured interval and serves the latest data at:

- **Metrics:** `http://<addon>:8099/v1/metrics`
- **Health:** `http://<addon>:8099/v1/health`
- **API docs:** `http://<addon>:8099/docs`

## Home Assistant Sensors

Add REST sensors to your `configuration.yaml`:

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
        value_template: '{{ value_json.daily_energy_kwh }}'
        unit_of_measurement: 'kWh'
        device_class: energy
        state_class: total_increasing
```

See the [full README](https://github.com/ashwhall/ha-sems-plus-addon) for all available sensor examples.

## Security

- Credentials are stored securely in Home Assistant's add-on options.
- The API is unauthenticated — **do not expose port 8099 to the internet.**
- No sensitive data is written to logs.
