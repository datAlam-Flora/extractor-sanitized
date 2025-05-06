from datetime import datetime, timedelta
import json

# ✅ Load credentials from JSON file
with open("credentials.json", "r") as f:
    credentials = json.load(f)

# ✅ Example: Get credentials for a specific site (change as needed)
site_url = "https://aw8.premium-bo.com"
creds = credentials.get(site_url, {})

# ✅ Get yesterday's datetime range (Base UTC Time)
yesterday = datetime.now() - timedelta(days=1)
yesterday_dt = {
    "start": yesterday.replace(hour=0, minute=0, second=0, microsecond=0),
    "end": yesterday.replace(hour=23, minute=59, second=59, microsecond=0),
}

print(f"📅 Base datetime range (UTC): {yesterday_dt['start']} to {yesterday_dt['end']}\n")

# ✅ Dictionary to store country-specific datetime ranges
country_timezones = {}

# ✅ Extract time offsets for each country
for brand, details in creds.items():
    if isinstance(details, list):  # Ensure the value is a list (brand details)
        country = details[1]  # Extract country name
        try:
            time_offset = int(details[2])  # Convert offset to integer
        except ValueError:
            print(f"⚠️ Invalid time offset for {brand}. Skipping...")
            continue

        # ✅ Calculate country-specific datetime range
        country_dt = {
            "start": yesterday_dt["start"] + timedelta(hours=time_offset),
            "end": yesterday_dt["end"] + timedelta(hours=time_offset),
        }

        # ✅ Store in dictionary (to avoid duplicate country calculations)
        if country not in country_timezones:
            country_timezones[country] = country_dt

# ✅ Print datetime ranges for each country
for country, dt_range in country_timezones.items():
    print(f"🌍 {country} datetime range: {dt_range['start']} to {dt_range['end']}")
