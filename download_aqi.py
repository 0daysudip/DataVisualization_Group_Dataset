import requests
import pandas as pd
import time
import os
from datetime import datetime

API_KEY  = "740f633ad635cd04b04da31d3b416a70f28c10c12de5c223570e6dd436f65bbf"
HEADERS  = {"X-API-Key": API_KEY}
BASE_URL = "https://api.openaq.org/v3"
LIMIT    = 1000

STATIONS = [
    {
        "id"  : 5506835,
        "name": "Gaushala_Kathmandu",
        "city": "Kathmandu",
        "lat" : 27.7089,
        "lon" : 85.3397,
        "file": r"C:\Users\asus\Desktop\New_Dataset\AQI_Gaushala_Kathmandu.csv",
    },
    {
        "id"  : 6097220,
        "name": "Pokhara_Ward7",
        "city": "Pokhara",
        "lat" : 28.2096,
        "lon" : 83.9856,
        "file": r"C:\Users\asus\Desktop\New_Dataset\AQI_Pokhara_Ward7.csv",
    },
    {
        "id"  : 6108844,
        "name": "Birendranagar_Surkhet",
        "city": "Birendranagar",
        "lat" : 28.6000,
        "lon" : 81.6167,
        "file": r"C:\Users\asus\Desktop\New_Dataset\AQI_Birendranagar_Surkhet.csv",
    },
]

DATE_FROM = "2025-10-01T00:00:00Z"
DATE_TO   = "2026-07-14T23:59:59Z"

os.makedirs(r"C:\Users\asus\Desktop\New_Dataset", exist_ok=True)

def get_sensors(location_id):
    r = requests.get(
        f"{BASE_URL}/locations/{location_id}/sensors",
        headers=HEADERS,
        timeout=30
    )
    return r.json().get("results", [])

def download_sensor(sensor_id):
    all_records = []
    page        = 1

    while True:
        try:
            r = requests.get(
                f"{BASE_URL}/sensors/{sensor_id}/measurements",
                headers=HEADERS,
                params={
                    "date_from": DATE_FROM,
                    "date_to"  : DATE_TO,
                    "limit"    : LIMIT,
                    "page"     : page,
                },
                timeout=30,
            )

            if r.status_code == 429:
                print("    Rate limited. Waiting 60s...")
                time.sleep(60)
                continue
            if r.status_code != 200:
                print(f"    Error {r.status_code}. Skipping.")
                break

            results = r.json().get("results", [])
            if not results:
                break

            for rec in results:
                all_records.append({
                    "sensor_id"     : sensor_id,
                    "value"         : rec.get("value"),
                    "datetime_utc"  : (rec.get("period") or {}).get("datetimeTo", {}).get("utc", ""),
                    "datetime_local": (rec.get("period") or {}).get("datetimeTo", {}).get("local", ""),
                })

            print(f"      Page {page} — {len(all_records):,} rows")

            if len(results) < LIMIT:
                break

            page += 1
            time.sleep(0.3)

        except Exception as e:
            print(f"    Error: {e}. Retrying...")
            time.sleep(10)

    return all_records

def download_station(station):
    print(f"\n{'='*55}")
    print(f"  Station  : {station['name']}")
    print(f"  ID       : {station['id']}")
    print(f"{'='*55}")

    sensors = get_sensors(station["id"])
    print(f"  Sensors found: {len(sensors)}")

    all_records = []

    for sensor in sensors:
        sensor_id    = sensor.get("id")
        sensor_name  = (sensor.get("parameter") or {}).get("name", "")
        sensor_units = (sensor.get("parameter") or {}).get("units", "")

        print(f"\n    Sensor {sensor_id} — {sensor_name} ({sensor_units})")
        records = download_sensor(sensor_id)

        for rec in records:
            rec["parameter"]      = sensor_name
            rec["units"]          = sensor_units
            rec["parameter_unit"] = f"{sensor_name} ({sensor_units})"
            rec["location_id"]    = station["id"]
            rec["location_name"]  = station["name"]
            rec["city"]           = station["city"]
            rec["latitude"]       = station["lat"]
            rec["longitude"]      = station["lon"]
            rec["source"]         = f"OpenAQ v3 — https://explore.openaq.org/locations/{station['id']}"
            rec["downloaded_at"]  = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        all_records.extend(records)

    if not all_records:
        print("  No records. Skipping.")
        return

    df = pd.DataFrame(all_records)

    df["datetime_utc"]   = pd.to_datetime(df["datetime_utc"],   utc=True,   errors="coerce")
    df["datetime_local"] = pd.to_datetime(df["datetime_local"],              errors="coerce")

    df["date"]       = df["datetime_utc"].dt.date
    df["year"]       = df["datetime_utc"].dt.year
    df["month"]      = df["datetime_utc"].dt.month
    df["year_month"] = df["datetime_utc"].dt.to_period("M").astype(str)

    df = df[df["value"].notna()]
    df = df[df["value"] > 0]

    df = df.sort_values("datetime_utc").reset_index(drop=True)

    df.to_csv(station["file"], index=False)

    print(f"\n  SAVED    : {station['file']}")
    print(f"  Rows     : {len(df):,}")
    print(f"  Params   : {df['parameter'].unique().tolist()}")
    print(f"  Date from: {df['datetime_utc'].min()}")
    print(f"  Date to  : {df['datetime_utc'].max()}")

for station in STATIONS:
    download_station(station)

print("\n" + "="*55)
print("="*55)