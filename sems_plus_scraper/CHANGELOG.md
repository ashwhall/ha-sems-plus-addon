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
