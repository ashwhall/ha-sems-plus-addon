# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] — 2026-03-25

### Added

- Initial release
- Playwright-based headless Chromium scraper for semsplus.goodwe.com
- FastAPI HTTP API with versioned endpoints (`/v1/metrics`, `/v1/health`)
- Configurable poll interval (60–3600 seconds, default 300)
- Session cookie persistence across restarts
- Multi-arch support (amd64, aarch64)
- Placeholder CSS selectors (to be replaced with real selectors)

## [0.1.1] — 2026-03-25

### Added
- Real CSS selectors for all available SEMS+ metrics
- Dockerfile and S6-overlay for Home Assistant add-on compatibility
- Home Assistant REST sensor integration example
- Improved error handling and debug logging

## [0.1.2] — 2026-03-25

### Changed
- Improved null/zero handling for missing metrics
- Updated documentation and sample configuration to match all available API outputs

## [0.1.3] — 2026-03-25

### Fixed
- Fixed S6 double-start issue in Docker
- Increased wait time for dynamic content rendering
- Added debug HTML logging for missing metrics

## [0.1.4] — 2026-03-25

### Changed
- Synced README and configuration.sample.yaml with all PlantMetrics fields
- Bumped version for documentation and config updates

## [0.1.5] — 2026-03-25

### Changed
- Refactor: stateless browser per scrape for lowest memory usage
- SEMSScraper now launches and closes browser for each scrape
- Removes all persistent browser state and lifecycle
- Cookie persistence retained for login efficiency
- API continues to serve cached metrics only

## [0.1.6] — 2026-03-26

### Fixed
- Robust /metrics endpoint: never overwrites cached metrics with zeros
- Warns in logs if fields are missing or data is stale
- Only returns zeros for fields missing in last good scrape
- Improved logging for debugging missing/stale data
