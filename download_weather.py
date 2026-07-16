import requests
import pandas as pd
import os

LOCATIONS = [
    {
        "city": "Kathmandu",
        "lat" : 27.7172,
        "lon" : 85.3240,
        "file": r"C:\Users\asus\Desktop\New_Dataset\Weather_Kathmandu.csv",
    },
    {
        "city": "Pokhara",
        "lat" : 28.2096,
        "lon" : 83.9856,
        "file": r"C:\Users\asus\Desktop\New_Dataset\Weather_Pokhara.csv",
    },
    {
        "city": "Birendranagar",
        "lat" : 28.6000,
        "lon" : 81.6167,
        "file": r"C:\Users\asus\Desktop\New_Dataset\Weather_Birendranagar.csv",
    },
]

START_DATE = "2025-10-01"
END_DATE   = "2026-07-14"

os.makedirs(r"C:\Users\asus\Desktop\New_Dataset", exist_ok=True)

for loc in LOCATIONS:
    print(f"\nDownloading weather for {loc['city']}...")

    r = requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params={
            "latitude"  : loc["lat"],
            "longitude" : loc["lon"],
            "start_date": START_DATE,
            "end_date"  : END_DATE,
            "daily"     : [
                "temperature_2m_mean",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "relative_humidity_2m_mean",
                "windspeed_10m_max",
            ],
            "timezone"  : "Asia/Kathmandu",
        },
        timeout=30
    )

    data = r.json()

    if "daily" not in data:
        print(f"  ERROR: {data}")
        continue

    df = pd.DataFrame(data["daily"])
    df.columns = [
        "date",
        "temp_mean_c",
        "temp_max_c",
        "temp_min_c",
        "rainfall_mm",
        "humidity_pct",
        "windspeed_kmh",
    ]

    df["city"]      = loc["city"]
    df["latitude"]  = loc["lat"]
    df["longitude"] = loc["lon"]
    df["source"]    = "Open-Meteo Historical Weather API (open-meteo.com)"
    df["date"]       = pd.to_datetime(df["date"])
    df["year"]       = df["date"].dt.year
    df["month"]      = df["date"].dt.month
    df["year_month"] = df["date"].dt.to_period("M").astype(str)
    df = df.dropna()

    df.to_csv(loc["file"], index=False)

    print(f"  Saved  : {loc['file']}")
    print(f"  Rows   : {len(df):,}")
    print(f"  Temp   : {df['temp_mean_c'].mean():.1f}°C average")
    print(f"  Rain   : {df['rainfall_mm'].sum():.1f}mm total")
    print(f"  Range  : {df['date'].min().date()} to {df['date'].max().date()}")

print("\n" + "="*55)
print("="*55)