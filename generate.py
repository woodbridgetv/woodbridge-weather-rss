
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

LAT = 40.5536
LON = -74.2824
HEADERS = {
    "User-Agent": "WoodbridgeWeatherRSS/1.0 (public forecast feed)",
    "Accept": "application/geo+json"
}

def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

# Get NOAA forecast for Woodbridge
point = get_json(f"https://api.weather.gov/points/{LAT},{LON}")
forecast_url = point["properties"]["forecast"]
forecast = get_json(forecast_url)

periods = forecast["properties"]["periods"]
days = {}

for p in periods:
    start = datetime.fromisoformat(p["startTime"]).astimezone(
        ZoneInfo("America/New_York")
    )
    key = start.date()

    if key not in days:
        days[key] = {
            "high": None,
            "low": None,
            "conditions": []
        }

    day = days[key]
    temp = p["temperature"]

    if p["isDaytime"]:
        day["high"] = temp
        day["conditions"].append(p["shortForecast"])
    else:
        day["low"] = temp
        if not day["conditions"]:
            day["conditions"].append(p["shortForecast"])

# Create RSS feed
rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")

ET.SubElement(channel, "title").text = "Woodbridge NJ 7-Day Weather"
ET.SubElement(channel, "link").text = "https://www.weather.gov/"
ET.SubElement(channel, "description").text = "NOAA forecast for Woodbridge, New Jersey"

for date, data in sorted(days.items())[:7]:
    title = date.strftime("%A").upper()

    high = f'{data["high"]}°F' if data["high"] is not None else "N/A"
    low = f'{data["low"]}°F' if data["low"] is not None else "N/A"
    conditions = data["conditions"][0] if data["conditions"] else "Forecast unavailable"

    description = f'{conditions} | High {high} | Low {low}'

    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = f"WOODBRIDGE {title}"
    ET.SubElement(item, "description").text = description
    ET.SubElement(item, "guid").text = f"woodbridge-weather-{date.isoformat()}"

Path("docs").mkdir(exist_ok=True)
ET.ElementTree(rss).write(
    "docs/feed.xml",
    encoding="utf-8",
    xml_declaration=True
)

print("Woodbridge weather RSS feed generated successfully.")
