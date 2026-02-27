"""
data_sources.py — Fetchers for OpenWeatherMap, USGS, NASA FIRMS, Open-Meteo
"""
import httpx
import os
import csv
import io
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY", "")
NASA_FIRMS_KEY  = os.getenv("NASA_FIRMS_MAP_KEY", "")

KENYA_BBOX = {  # min_lat, min_lng, max_lat, max_lng
    "min_lat": -4.68, "max_lat": 5.02,
    "min_lng": 33.91, "max_lng": 41.90
}


async def fetch_weather(county_name: str, lat: float, lng: float) -> dict:
    """Fetch current weather for a county centroid."""
    if not OPENWEATHER_KEY:
        return _mock_weather(county_name)
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lng}&appid={OPENWEATHER_KEY}&units=metric"
    )
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                d = resp.json()
                return {
                    "county":      county_name,
                    "lat":         lat, "lng": lng,
                    "temp_c":      d["main"]["temp"],
                    "humidity":    d["main"]["humidity"],
                    "wind_speed":  d["wind"]["speed"],
                    "description": d["weather"][0]["description"],
                    "rainfall_mm": d.get("rain", {}).get("1h", 0),
                }
    except Exception as e:
        print(f"[Weather] Error for {county_name}: {e}")
    return _mock_weather(county_name)


def _mock_weather(county_name: str) -> dict:
    import random
    return {
        "county":       county_name,
        "temp_c":       random.uniform(18, 38),
        "humidity":     random.randint(30, 95),
        "wind_speed":   random.uniform(0, 15),
        "description":  random.choice(["clear sky", "heavy rain", "overcast clouds", "thunderstorm"]),
        "rainfall_mm":  random.uniform(0, 50),
        "mock":         True,
    }


async def fetch_earthquakes() -> list[dict]:
    """Fetch recent earthquakes in Kenya/East Africa from USGS."""
    url = (
        "https://earthquake.usgs.gov/fdsnws/event/1/query"
        f"?format=geojson&minmagnitude=2.5"
        f"&minlatitude={KENYA_BBOX['min_lat']}&maxlatitude={KENYA_BBOX['max_lat']}"
        f"&minlongitude={KENYA_BBOX['min_lng']}&maxlongitude={KENYA_BBOX['max_lng']}"
        "&orderby=time&limit=20"
    )
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for feat in data.get("features", []):
                    props = feat["properties"]
                    coords = feat["geometry"]["coordinates"]
                    results.append({
                        "magnitude": props["mag"],
                        "place":     props["place"],
                        "time":      props["time"],
                        "lat":       coords[1],
                        "lng":       coords[0],
                        "depth_km":  coords[2],
                        "severity":  "High" if props["mag"] >= 5 else "Medium" if props["mag"] >= 3.5 else "Low",
                    })
                return results
    except Exception as e:
        print(f"[USGS] Error: {e}")
    return []


async def fetch_wildfires() -> list[dict]:
    """Fetch active wildfire hotspots from NASA FIRMS for Kenya."""
    if not NASA_FIRMS_KEY:
        return []
    url = (
        f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{NASA_FIRMS_KEY}/VIIRS_SNPP_NRT"
        f"/{KENYA_BBOX['min_lng']},{KENYA_BBOX['min_lat']},{KENYA_BBOX['max_lng']},{KENYA_BBOX['max_lat']}/1"
    )
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                reader = csv.DictReader(io.StringIO(resp.text))
                fires = []
                for row in reader:
                    try:
                        fires.append({
                            "lat":         float(row["latitude"]),
                            "lng":         float(row["longitude"]),
                            "brightness":  float(row.get("bright_ti4", 0)),
                            "confidence":  row.get("confidence", "nominal"),
                            "acq_date":    row.get("acq_date", ""),
                        })
                    except Exception:
                        continue
                return fires
    except Exception as e:
        print(f"[FIRMS] Error: {e}")
    return []


async def fetch_forecast(lat: float, lng: float) -> dict:
    """Fetch 7-day hourly forecast from Open-Meteo (no API key needed)."""
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lng}"
        f"&daily=precipitation_sum,temperature_2m_max,temperature_2m_min,windspeed_10m_max"
        f"&forecast_days=7&timezone=Africa%2FNairobi"
    )
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        print(f"[Open-Meteo] Error at ({lat},{lng}): {e}")
    return {}
