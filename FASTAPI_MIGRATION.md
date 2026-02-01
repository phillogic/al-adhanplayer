# Migration Plan: al-adhanplayer to FastAPI

This document outlines how to migrate the current Python script-based adhan player into a FastAPI service, following the patterns in the reference FastAPI app under `reference/tardis-spn-manager`.

## Goals

- Keep the core functionality: fetch daily prayer times and play an adhan at the scheduled times.
- Add a small HTTP API to control/observe the player (for n8n and other workflows).
- Keep Prometheus metrics available on port 8000 (now as `/metrics`).
- Maintain compatibility with current K3s deployment model and audio device setup inside the container.

## Current State Summary

- Entrypoint: `adhanPlayer.py` (single script)
  - Polls AlAdhan API for Sydney times
  - Uses `python-vlc` to play local audio files (`media/`, special case for `media/fajr`)
  - Exposes Prometheus metrics via `prometheus_client.start_http_server(8000)`
- Logging: `utils/adhanLogger.py` configures console + rotating file loggers
- Docker: Ubuntu base, installs ALSA, VLC, espeak, cron; runs `cron && python3 ./adhanPlayer.py`
- K8s: Single container Deployment with Service exposing port 8000 (currently the metrics endpoint)

## Target Architecture

FastAPI app with a background task that retains the scheduling/playing logic and exposes:

- Health endpoints: `/`, `/health`, `/health/ready` (aligned to reference patterns)
- Metrics endpoint: `/metrics` exporting the existing custom metrics
- Player/prayer endpoints for automation:
  - `GET /api/v1/prayer/times` – latest fetched times
  - `POST /api/v1/prayer/refresh` – force refresh from AlAdhan API
  - `GET /api/v1/player/status` – status of background loop and next events
  - `POST /api/v1/player/preview?prayer=...` – play a preview adhan for a given prayer
  - `POST /api/v1/player/mute|unmute|volume` – optional controls, if required

### Proposed Project Layout

```
app/
  __init__.py
  main.py                  # FastAPI app + lifespan + routers
  core/
    __init__.py
    logging_config.py      # Wrap existing utils/adhanLogger or integrate
  models/
    __init__.py
    prayer_models.py       # Pydantic models for responses
  routers/
    __init__.py
    diagnostics.py         # /, /health, /health/ready
    player.py              # player controls and status
    prayer.py              # times, refresh
  services/
    __init__.py
    prayer_service.py      # fetch times, calculate, gauges update
    player_service.py      # play audio via VLC, select files
  metrics/
    __init__.py
    registry.py            # Summary/Counter/Gauge and /metrics route

media/                     # unchanged
utils/adhanLogger.py       # reused by logging_config
```

### Lifespan and Background Task

- Use FastAPI `lifespan` to initialize services on startup:
  - Build a `PrayerService` that encapsulates:
    - `GetLatestPrayerTimes()` (ported to async-friendly or thread-safe sync)
    - `calculateTimeToPrayer()` and gauge updates
    - In-memory state: last timestamp, prayerTimes, adhanPlayed
  - Build a `PlayerService` that encapsulates VLC playback and file selection
- Start an asyncio background task that runs the main loop:
  - Refresh times if day changes
  - Check current time every 60s and trigger playback when within the window
  - Update gauges each iteration
- On shutdown, cancel the background task

### Metrics Export

- Keep existing custom metrics (same names) using `prometheus_client`.
- Replace `start_http_server(8000)` with a FastAPI route `/metrics`:
  - Use `prometheus_client.generate_latest()` within a Starlette response
  - Ensure the same CollectorRegistry or default registry is used by services

### Logging

- Reuse `utils/adhanLogger.py` via a small `app/core/logging_config.py` shim to keep consistent formatting and file rotation.
- Optionally align log levels with uvicorn.

### Configuration

Add environment variables (defaults preserved when possible):

- `TZ` – timezone (already set in Dockerfile)
- `PRAYER_CITY` – default `Sydney`
- `PRAYER_COUNTRY` – default `AU`
- `ALADHAN_METHOD` – default `1`
- `PLAY_WINDOW_MINUTES` – acceptable minutes delta to trigger adhan (default 2)
- `MEDIA_DIR` – default `media`
- `FAJR_SUBDIR` – default `media/fajr`
- `PORT` – app port (default 8000)
- `HOST` – host bind (default 0.0.0.0)

## API Surface (Initial)

- `GET /` – metadata and endpoints (like reference)
- `GET|HEAD /health` – app health (simple alive)
- `GET|HEAD /health/ready` – readiness (optionally check TCP reachability to AlAdhan or just internal state)
- `GET /metrics` – Prometheus exposition format
- `GET /api/v1/prayer/times` – latest times and timestamp
- `POST /api/v1/prayer/refresh` – refresh from API now
- `GET /api/v1/player/status` – shows next scheduled events and last playback
- `POST /api/v1/player/preview?prayer=fajr|dhuhr|asr|maghrib|isha` – test play

Auth: None initially (assumed cluster/internal use). We can add headers-based auth later following the reference patterns.

## Docker & K8s Changes

Dockerfile:
- Install new deps: `fastapi`, `uvicorn[standard]`, `prometheus_client`, `pydantic`.
- Keep ALSA/VLC/espeak/cron as-is.
- Replace CMD with: `cron && uvicorn app.main:app --host 0.0.0.0 --port 8000`.

K8s:
- No Service change required (still port 8000). Now `/metrics` is served by FastAPI instead of the raw Prometheus HTTP server.
- Optional: add livenessProbe/readinessProbe using `/health` and `/health/ready` HTTP checks.
- Retain current `securityContext` for audio device access.

## Step-by-Step Migration

1) Scaffold FastAPI app structure (`app/` folders as above)
2) Port logging to `app/core/logging_config.py` using `utils/adhanLogger`
3) Extract core functions from `adhanPlayer.py` into `app/services/prayer_service.py` and `app/services/player_service.py`
4) Implement background loop (async task) using the extracted services
5) Add routers for diagnostics (`/`, `/health`, `/health/ready`) and API endpoints
6) Add `/metrics` route using `prometheus_client` default registry
7) Keep metric names and update calls in services to avoid breaking Grafana dashboards
8) Update tests (unit tests for services + basic API tests where applicable)
9) Update Dockerfile to use `uvicorn`; keep cron-based white noise
10) Update K8s manifests to use HTTP probes (optional) and redeploy

## Testing Strategy

- Local: run `uvicorn app.main:app --reload` and hit `/docs`, `/metrics`.
- Audio: test `POST /api/v1/player/preview?prayer=asr` in a runtime with device access.
- Unit tests: port existing tests in `test/AdhanPlayerTest.py` to target `services/` functions.
- Smoke tests in cluster: verify `/health`, `/metrics`, and scheduled playback.

## Compatibility & Risks

- Metric names preserved; scrape path changes to `/metrics` (verify Prometheus scrape config if it previously scraped root).
- Audio device and permissions remain the main operational risk; continue using privileged context if needed.
- Timezone/DST correctness relies on container `TZ` as today.
- AlAdhan API errors already handled; continue logging and retry on next loop.

## Open Questions

- Do you want authentication on these endpoints? If yes, we can adopt the reference auth patterns later.
- Do you want to support geolocation or dynamic city/country via API/config now?
- Volume/mute controls desired via API?

## Rollout

1. Build and push new image tag
2. Deploy to a test namespace with the updated Deployment
3. Validate:
   - `/health`, `/health/ready`, `/metrics`
   - Scheduled playback and preview endpoint
   - Grafana panels still receive metrics
4. Rollout to prod namespace, keep previous image tag for rollback

## Timeline (rough)

- Day 1: Scaffold, port services, basic endpoints, metrics
- Day 2: Docker/K8s, tests, validation in cluster

---

If this plan looks good, I’ll proceed to scaffold the FastAPI app and wire up the background loop and endpoints.

