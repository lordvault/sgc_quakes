# SGC Quakes Colombia Add-on Documentation

Real-time earthquake monitoring for Colombia using data provided directly by the **Servicio Geológico Colombiano (SGC)**.

## Configuration Options

| Option | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `poll_interval` | Integer | `45` | Polling frequency in seconds (between 15 and 300 seconds). |
| `min_magnitude` | Float | `2.5` | Minimum magnitude threshold to trigger notifications and updates (0.0 - 10.0). |
| `max_distance_km` | Integer | `0` | Maximum distance (in km) from home coordinates. Set to `0` to monitor all events across Colombia. |
| `fetch_home_from_ha` | Boolean | `true` | Automatically fetch latitude & longitude from `zone.home` in Home Assistant. |
| `home_latitude` | Float | `0.0` | Optional manual latitude (used if `fetch_home_from_ha` is `false`). |
| `home_longitude` | Float | `0.0` | Optional manual longitude (used if `fetch_home_from_ha` is `false`). |

---

## Home Assistant Entities & Events

### 1. Sensor: `sensor.sgc_latest_earthquake`
* **State**: Magnitude of the latest qualifying earthquake (e.g. `5.1`).
* **Attributes**:
  * `place`: Epicenter location (e.g. `Los Santos - Santander, Colombia`).
  * `magnitude`: Numeric magnitude.
  * `depth_km`: Hypocenter depth in kilometers.
  * `distance_km`: Calculated distance from your Home zone.
  * `latitude`: Latitude of the epicenter.
  * `longitude`: Longitude of the epicenter.
  * `local_time`: Local Colombian time of the event.
  * `utc_time`: UTC timestamp of the event.
  * `closer_towns`: Nearby municipalities and distances.
  * `felt_reports`: Number of "felt it" community reports.
  * `status`: Verification status (`manual` or `automatic`).
  * `event_id`: Unique SGC event identifier.

### 2. Event: `sgc_earthquake_detected`
Fires on the Home Assistant Event Bus whenever a new earthquake meets your magnitude and distance filters.

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

## Automation Example

Send mobile push notifications when a new qualifying earthquake is detected:

```yaml
alias: "SGC Earthquake Alert"
description: "Send alert on phone when an earthquake is detected"
trigger:
  - platform: event
    event_type: sgc_earthquake_detected
action:
  - service: notify.notify
    data:
      title: "🚨 Sismo Detectado (M{{ trigger.event.data.magnitude }})"
      message: >
        Epicentro: {{ trigger.event.data.place }}
        Distancia: {{ trigger.event.data.distance_km }} km
        Profundidad: {{ trigger.event.data.depth_km }} km
        Hora local: {{ trigger.event.data.local_time }}
      data:
        priority: high
        channel: Emergency
```
