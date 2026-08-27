# Changelog

All notable changes to the **SGC Quakes Colombia** Home Assistant Add-on will be documented in this file.

## [1.0.3] - 2026-08-27

### 🚀 Improvements & Features
- **Max Event Age Filter**: Added `max_event_age_minutes` option (default: `60` minutes) to prevent alerts when SGC publishes retroactive manual reviews hours or days later.
- **Add-on Branding**: Added official icon and logo for the Home Assistant Add-on Store interface.
- **Changelog Support**: Added `CHANGELOG.md` tab for Home Assistant Supervisor UI.

### 🐛 Bug Fixes
- **Chronological Sorting**: Ensured the SGC GeoJSON feed is always sorted chronologically (oldest to newest) before processing so timestamps and states are evaluated strictly in order.
- **Safe ID Cache Pruning**: Fixed set pruning bug that could evict active IDs, ensuring events currently present in the 5-day SGC feed are never prematurely purged.
- **Sensor State Updates**: Allowed the latest earthquake sensor entity (`sensor.sgc_latest_earthquake`) to update attributes (e.g. manual status, felt report counts) when SGC updates an existing event, without firing duplicate notification events.

---

## [1.0.2] - 2026-08-26

### 🐛 Bug Fixes
- **S6-Overlay Compatibility**: Set `init: false` in `config.yaml` to prevent Docker init (`tini`) injection and fix the `s6-overlay-suexec: fatal: can only run as pid 1` startup error.

---

## [1.0.1] - 2026-08-26

### 🚀 Improvements
- **Multi-Architecture Support**: Added `build.yaml` mapping official Home Assistant base images for `aarch64`, `amd64`, `armhf`, `armv7`, and `i386`.

---

## [1.0.0] - 2026-08-26

### 🎉 Initial Release
- Direct connection to Servicio Geológico Colombiano (SGC) 5-day GeoJSON summary feed.
- Automatic location detection and distance calculation from Home Assistant `zone.home`.
- Custom magnitude threshold (`min_magnitude`) and distance radius (`max_distance_km`) filters.
- Publishes latest event to `sensor.sgc_latest_earthquake` with rich attributes.
- Dispatches `sgc_earthquake_detected` events on the Home Assistant Event Bus for automations.
