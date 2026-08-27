# Project Context: SGC Quakes Colombia Home Assistant Add-on

## 1. Project Overview
- **Name**: SGC Quakes Colombia (`sgc_quakes`)
- **GitHub Repository**: https://github.com/lordvault/sgc_quakes
- **Maintainer**: `lordvault` (GitHub handle)
- **Primary Function**: Real-time earthquake monitoring for Colombia using the open GeoJSON feed from the **Servicio Geológico Colombiano (SGC)**.

---

## 2. Architecture & Home Assistant Add-on Rules

### Repository Layout
```text
sgc_quakes/ (Repository Root)
├── .gitignore
├── repository.yaml          <-- REQUIRED for Home Assistant Add-on Store
├── README.md                <-- GitHub README with installation instructions & automation examples
├── CHANGELOG.md             <-- Root changelog for GitHub
├── GEMINI.md                <-- Workspace context for AI agents
└── sgc_quakes/              <-- Add-on directory
    ├── config.yaml          <-- Add-on metadata and configuration schema
    ├── build.yaml           <-- Multi-architecture base image mappings
    ├── Dockerfile           <-- Alpine-based container specification
    ├── run.sh               <-- S6-overlay entrypoint script
    ├── app.py               <-- Polling daemon and Home Assistant REST bridge
    ├── icon.png             <-- Add-on icon (512x512) for Home Assistant UI
    ├── logo.png             <-- Add-on logo for Home Assistant UI
    ├── CHANGELOG.md         <-- Add-on changelog tab for Home Assistant UI
    └── DOCS.md              <-- Add-on documentation tab for Home Assistant UI
```

### Critical Home Assistant Build & Runtime Requirements
1. **`init: false` in `config.yaml` is MANDATORY**:
   - Home Assistant base images use **S6-Overlay v3**.
   - If `init: false` is omitted, Home Assistant Supervisor injects Docker's `--init` (tini), preventing S6-Overlay from being PID 1 and causing `s6-overlay-suexec: fatal: can only run as pid 1`.
2. **Base Image Specifications**:
   - Official multi-arch base image: `ghcr.io/home-assistant/base:latest` (supports `aarch64` and `amd64`).
   - Legacy 32-bit base images: `ghcr.io/home-assistant/armhf-base:latest`, `ghcr.io/home-assistant/armv7-base:latest`, `ghcr.io/home-assistant/i386-base:latest`.
   - `build.yaml` in the `sgc_quakes/` folder defines these mappings for Supervisor builds.
   - Never use non-existent registries such as `ghcr.io/home-assistant/alpine`.
3. **Container Entrypoint**:
   - `run.sh` must use shebang `#!/usr/bin/with-contenv bashio` to import `SUPERVISOR_TOKEN` and environment variables.
   - Python is executed with `exec python3 -u /app.py` for unbuffered logging and clean signal propagation.

---

## 3. Data Source Quirks & API Specifics

- **Endpoint**: `https://archive.sgc.gov.co/feed/v1.0.1/summary/five_days_all.json`
- **Coordinate Order Quirk**: SGC GeoJSON violates standard RFC 7946 by sending coordinates as `[latitude, longitude, depth]` (`[6.8215, -73.114, 149.0]`) instead of standard `[lon, lat, depth]`.
  - In Colombia, Latitude is positive (~0° to 13° N) and Longitude is negative (~-66° to -79° W).
  - Always use `parse_coordinates()` in `app.py` to auto-detect coordinate order.
- **Key Properties in SGC Feed**:
  - `utcTime`: UTC timestamp string (`"YYYY-MM-DD HH:MM"`)
  - `localTime`: Local Colombian time string (`"YYYY-MM-DD HH:MM"`)
  - `mag`: Magnitude (float)
  - `place`: Descriptive location string
  - `closerTowns`: Nearby towns with distances
  - `felt`: Number of community felt reports
  - `status`: Verification status (`"manual"` or `"automatic"`)

---

## 4. Home Assistant Integration

- **Authentication**: `homeassistant_api: true` grants access to `http://supervisor/core/api` via `Bearer {SUPERVISOR_TOKEN}`.
- **Sensor**: `sensor.sgc_latest_earthquake`
  - State: numeric magnitude
  - Attributes: `place`, `distance_km`, `depth_km`, `latitude`, `longitude`, `local_time`, `utc_time`, `closer_towns`, `felt_reports`, `status`, `event_id`
- **Event**: `sgc_earthquake_detected`
  - Fired on the Home Assistant Event Bus whenever a new earthquake meets `min_magnitude` and `max_distance_km` filters.
- **Startup Behavior**: On initial startup, the latest qualifying historical event populates `sensor.sgc_latest_earthquake` without firing notification events.

---

## 5. Privacy & Security Rules
- **DO NOT** commit or expose personal real names or email addresses.
- Git commits must use username `lordvault` and email `lordvault@users.noreply.github.com`.
