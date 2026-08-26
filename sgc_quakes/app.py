import os
import json
import time
import math
import logging
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

SGC_URL = "https://archive.sgc.gov.co/feed/v1.0.1/summary/five_days_all.json"
HA_URL = "http://supervisor/core/api"
SUPERVISOR_TOKEN = os.getenv("SUPERVISOR_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {SUPERVISOR_TOKEN}",
    "Content-Type": "application/json"
}

def load_options():
    try:
        with open("/data/options.json", "r") as f:
            return json.load(f)
    except Exception as e:
        logging.warning(f"Could not load /data/options.json, using defaults. Error: {e}")
        return {
            "poll_interval": 45,
            "min_magnitude": 2.5,
            "max_distance_km": 0,
            "home_latitude": 0.0,
            "home_longitude": 0.0,
            "fetch_home_from_ha": True
        }

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def get_home_coordinates():
    try:
        resp = requests.get(f"{HA_URL}/states/zone.home", headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            lat = data.get("attributes", {}).get("latitude")
            lon = data.get("attributes", {}).get("longitude")
            if lat is not None and lon is not None:
                logging.info(f"Loaded Home coordinates from HA: Lat {lat}, Lon {lon}")
                return float(lat), float(lon)
    except Exception as e:
        logging.error(f"Failed to fetch zone.home coordinates: {e}")
    return None, None

def post_ha_state(entity_id, state_value, attributes):
    try:
        payload = {
            "state": str(state_value),
            "attributes": attributes
        }
        res = requests.post(f"{HA_URL}/states/{entity_id}", headers=HEADERS, json=payload, timeout=10)
        return res.status_code in (200, 201)
    except Exception as e:
        logging.error(f"Error posting state to {entity_id}: {e}")
        return False

def fire_ha_event(event_type, event_data):
    try:
        requests.post(f"{HA_URL}/events/{event_type}", headers=HEADERS, json=event_data, timeout=10)
    except Exception as e:
        logging.error(f"Error firing HA event {event_type}: {e}")

def parse_coordinates(coords):
    """
    SGC feed returns [lat, lon, depth] in coordinates instead of standard [lon, lat, depth].
    Handle both formats gracefully.
    """
    if len(coords) < 2:
        return 0.0, 0.0, 0.0
    c0 = float(coords[0])
    c1 = float(coords[1])
    depth = float(coords[2]) if len(coords) > 2 else 0.0
    
    if c0 < 0 and c1 > 0:
        lon, lat = c0, c1
    else:
        lat, lon = c0, c1
    return lat, lon, depth

def main():
    options = load_options()
    poll_interval = int(options.get("poll_interval", 45))
    min_magnitude = float(options.get("min_magnitude", 2.5))
    max_distance = float(options.get("max_distance_km", 0))

    home_lat = float(options.get("home_latitude", 0.0))
    home_lon = float(options.get("home_longitude", 0.0))

    if options.get("fetch_home_from_ha", True):
        ha_lat, ha_lon = get_home_coordinates()
        if ha_lat is not None and ha_lon is not None:
            home_lat, home_lon = ha_lat, ha_lon

    seen_event_ids = set()
    first_run = True

    logging.info(
        f"SGC Monitor started. Min Mag: {min_magnitude} | Max Dist: {max_distance} km | "
        f"Home: ({home_lat}, {home_lon}) | Poll: {poll_interval}s"
    )

    while True:
        try:
            req_headers = {"User-Agent": "HomeAssistant-SGC-Quakes-Addon"}
            resp = requests.get(SGC_URL, headers=req_headers, timeout=15)
            if resp.status_code == 200:
                feed = resp.json()
                features = feed.get("features", [])

                latest_qualifying_event = None

                for feat in reversed(features):
                    props = feat.get("properties", {})
                    geom = feat.get("geometry", {})
                    coords = geom.get("coordinates", [0, 0, 0])

                    event_id = feat.get("id") or props.get("id_sismo") or props.get("event_id")
                    if not event_id:
                        continue

                    lat, lon, depth = parse_coordinates(coords)
                    mag = float(props.get("mag") or props.get("magnitude") or props.get("magnitud") or 0.0)
                    
                    municipio = props.get("municipio", "")
                    departamento = props.get("departamento", "")
                    place = props.get("place") or f"{municipio}, {departamento}".strip(", ")
                    utc_time = props.get("utcTime") or props.get("time") or props.get("hora_utc") or ""
                    local_time = props.get("localTime") or ""
                    closer_towns = props.get("closerTowns") or ""
                    felt_reports = props.get("felt") or 0
                    status = props.get("status") or ""

                    distance = 0.0
                    if home_lat != 0.0 or home_lon != 0.0:
                        distance = haversine_distance(home_lat, home_lon, lat, lon)

                    mag_qualifies = mag >= min_magnitude
                    dist_qualifies = (max_distance == 0) or (distance <= max_distance)

                    event_data = {
                        "id": event_id,
                        "magnitude": mag,
                        "place": place,
                        "depth_km": depth,
                        "distance_km": distance,
                        "latitude": lat,
                        "longitude": lon,
                        "utc_time": utc_time,
                        "local_time": local_time,
                        "closer_towns": closer_towns,
                        "felt_reports": felt_reports,
                        "status": status
                    }

                    if mag_qualifies and dist_qualifies:
                        latest_qualifying_event = event_data

                    if event_id not in seen_event_ids:
                        seen_event_ids.add(event_id)

                        if not first_run and mag_qualifies and dist_qualifies:
                            logging.info(
                                f"🚨 Qualifying Earthquake Detected! Mag {mag} - {place} "
                                f"({distance} km away, depth {depth} km)"
                            )
                            
                            fire_ha_event("sgc_earthquake_detected", event_data)

                            post_ha_state(
                                "sensor.sgc_latest_earthquake",
                                mag,
                                {
                                    "friendly_name": "SGC Último Sismo",
                                    "unit_of_measurement": "M",
                                    "icon": "mdi:waveform",
                                    **event_data
                                }
                            )

                # On first run, initialize sensor state with the most recent qualifying earthquake
                if first_run and latest_qualifying_event:
                    logging.info(
                        f"Initial sensor state populated with latest event: "
                        f"Mag {latest_qualifying_event['magnitude']} - {latest_qualifying_event['place']}"
                    )
                    post_ha_state(
                        "sensor.sgc_latest_earthquake",
                        latest_qualifying_event["magnitude"],
                        {
                            "friendly_name": "SGC Último Sismo",
                            "unit_of_measurement": "M",
                            "icon": "mdi:waveform",
                            **latest_qualifying_event
                        }
                    )

                first_run = False

                # Keep seen_event_ids manageable
                if len(seen_event_ids) > 2000:
                    seen_event_ids = set(list(seen_event_ids)[-1000:])

        except Exception as err:
            logging.error(f"Polling loop error: {err}")

        time.sleep(poll_interval)

if __name__ == "__main__":
    main()
