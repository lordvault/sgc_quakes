# SGC Quakes Colombia 🇨🇴 — Home Assistant Add-on

[![Open your Home Assistant instance and show the add-on store with a specific repository configured.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Flordvault%2Fsgc_quakes)

Real-time earthquake monitoring for Colombia using official seismic data provided directly by the **Servicio Geológico Colombiano (SGC)**.

---

## Features

- 📡 **Direct SGC Feed**: Polls the official GeoJSON summary endpoint from SGC.
- 📍 **Automatic Location & Distance Calculation**: Automatically reads your `zone.home` coordinates from Home Assistant to compute the exact distance (km) to the earthquake epicenter using the Haversine formula.
- 🎯 **Custom Threshold Filters**: Filter alerts by minimum magnitude (e.g., $M \ge 2.5$) and maximum radius from your home.
- 📊 **Rich Sensor State**: Publishes the latest earthquake data to `sensor.sgc_latest_earthquake` with rich attributes (epicenter, depth, distance, local time, nearby towns, felt reports).
- ⚡ **Event Bus Integration**: Dispatches `sgc_earthquake_detected` events to trigger instant automations (push notifications, sirens, TTS announcements).

---

## Installation

### Method 1: Add via GitHub URL in Home Assistant (Recommended)

1. In Home Assistant, navigate to **Settings** > **Add-ons** > **Add-on Store**.
2. Click the **three vertical dots (⋮)** in the top-right corner and select **Repositories**.
3. In the **Add** input field, paste the repository URL:
   ```text
   https://github.com/lordvault/sgc_quakes
   ```
4. Click **Add**, then click **Close**.
5. Click the three dots (**⋮**) > **Check for updates** (or refresh your browser).
6. Find **SGC Quakes Colombia** under the *SGC Quakes Colombia Add-on Repository* section.
7. Click on the add-on card and click **Install**.
8. Go to the **Configuration** tab, customize your thresholds, and click **Save**.
9. In the **Info** tab, click **Start**, and optionally enable **Start on boot** and **Watchdog**.

---

### Method 2: One-Click via My Home Assistant

If you have [My Home Assistant](https://my.home-assistant.io/) configured, click the badge below:

[![Add Repository to Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Flordvault%2Fsgc_quakes)

---

### Method 3: Manual Installation (Local `/addons` folder)

1. Clone or download this repository.
2. Copy the `sgc_quakes` subfolder into your Home Assistant `/addons/` directory.
3. In Home Assistant, go to **Settings** > **Add-ons** > **Add-on Store**.
4. Click the three dots (**⋮**) > **Check for updates**.
5. Find **SGC Quakes Colombia** under *Local Add-ons* and click **Install**.

---

## Configuration

In the Add-on's **Configuration** tab, you can adjust the following options:

| Option | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `poll_interval` | Integer | `45` | Polling frequency in seconds (between 15 and 300). |
| `min_magnitude` | Float | `2.5` | Minimum magnitude to trigger events and updates (0.0 to 10.0). |
| `max_distance_km` | Integer | `0` | Max distance in km from your home. Set to `0` to monitor all events across Colombia. |
| `max_event_age_minutes` | Integer | `60` | Maximum age of earthquake in minutes to trigger real-time alert events (prevents alerts for retroactive events). Set to `0` for no limit. |
| `fetch_home_from_ha` | Boolean | `true` | Automatically fetch home coordinates from `zone.home`. |
| `home_latitude` | Float | `0.0` | Manual latitude (used if `fetch_home_from_ha` is `false`). |
| `home_longitude` | Float | `0.0` | Manual longitude (used if `fetch_home_from_ha` is `false`). |

---

## Entities & Events

### Sensor: `sensor.sgc_latest_earthquake`

| Property | Value Example |
| :--- | :--- |
| **State** | `5.1` (Magnitude) |
| **friendly_name** | `SGC Último Sismo` |
| **unit_of_measurement** | `M` |
| **place** | `Los Santos - Santander, Colombia` |
| **distance_km** | `257.5` |
| **depth_km** | `149.0` |
| **latitude** | `6.8215` |
| **longitude** | `-73.114` |
| **local_time** | `2026-08-26 11:45` |
| **utc_time** | `2026-08-26 16:45` |
| **closer_towns** | `Los Santos (Santander) a 7 km, Jordán (Santander) a 10 km, Zapatoca (Santander) a 17 km` |
| **felt_reports** | `2695` |
| **status** | `manual` |
| **event_id** | `SGC2026quikpc` |

---

### Event: `sgc_earthquake_detected`

Fired on the Home Assistant event bus whenever a qualifying earthquake is detected.

#### Event Data Payload:
```json
{
  "id": "SGC2026quikpc",
  "magnitude": 5.1,
  "place": "Los Santos - Santander, Colombia",
  "depth_km": 149.0,
  "distance_km": 257.5,
  "latitude": 6.8215,
  "longitude": -73.114,
  "local_time": "2026-08-26 11:45",
  "utc_time": "2026-08-26 16:45",
  "closer_towns": "Los Santos (Santander) a 7 km, Jordán (Santander) a 10 km, Zapatoca (Santander) a 17 km",
  "felt_reports": 2695,
  "status": "manual"
}
```

---

## Automation Examples

### 1. Mobile Push Notification
Send an alert with sound and critical priority to all mobile devices when an earthquake occurs:

```yaml
alias: "SGC Earthquake Notification"
description: "Send push alert on smartphone when an earthquake is detected"
trigger:
  - platform: event
    event_type: sgc_earthquake_detected
action:
  - service: notify.notify
    data:
      title: "🚨 Sismo Detectado M{{ trigger.event.data.magnitude }}"
      message: >
        Lugar: {{ trigger.event.data.place }}
        Distancia: {{ trigger.event.data.distance_km }} km
        Profundidad: {{ trigger.event.data.depth_km }} km
        Hora: {{ trigger.event.data.local_time }}
      data:
        priority: high
        ttl: 0
```

### 2. TTS Voice Announcement on Smart Speakers
Announce nearby earthquakes on smart speakers (e.g. Google Nest / Alexa):

```yaml
alias: "SGC Earthquake Voice Announcement"
description: "Announce earthquake on speaker if within 150km"
trigger:
  - platform: event
    event_type: sgc_earthquake_detected
condition:
  - condition: template
    value_template: "{{ trigger.event.data.distance_km <= 150 }}"
action:
  - service: tts.speak
    target:
      entity_id: tts.piper # or tts.google_en_com
    data:
      media_player_entity_id: media_player.living_room_speaker
      message: >
        Atención. Se ha detectado un sismo de magnitud {{ trigger.event.data.magnitude }} 
        en {{ trigger.event.data.place }}, a {{ trigger.event.data.distance_km }} kilómetros de distancia.
```

---

## Dashboard Card Example

You can display the latest earthquake on your Home Assistant dashboard using an Entities card or Markdown card:

```yaml
type: entities
title: 🇨🇴 SGC Monitoreo Sísmico
entities:
  - entity: sensor.sgc_latest_earthquake
    name: Magnitud
  - type: attribute
    entity: sensor.sgc_latest_earthquake
    attribute: place
    name: Epicentro
  - type: attribute
    entity: sensor.sgc_latest_earthquake
    attribute: distance_km
    name: Distancia
    unit: km
  - type: attribute
    entity: sensor.sgc_latest_earthquake
    attribute: depth_km
    name: Profundidad
    unit: km
  - type: attribute
    entity: sensor.sgc_latest_earthquake
    attribute: local_time
    name: Hora Local
```

---

## Data Source & Disclaimer

Data is retrieved from the [Servicio Geológico Colombiano (SGC)](https://www.sgc.gov.co) open feed. This project is an independent community add-on and is not officially affiliated with or endorsed by the SGC.
