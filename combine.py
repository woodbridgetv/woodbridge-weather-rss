
import xml.etree.ElementTree as ET
from pathlib import Path
from copy import deepcopy
from urllib.request import urlopen

WEATHER_FILE = Path("docs/feed.xml")
OUTPUT_FILE = Path("docs/community-feed.xml")

HISTORY_FEED_URL = (
    "https://woodbridgetv.github.io/nj-history-daily/feed.xml"
)

# Read the weather feed
weather_tree = ET.parse(WEATHER_FILE)
weather_channel = weather_tree.getroot().find("channel")

if weather_channel is None:
    raise ValueError("Weather RSS feed has no channel.")

# Create the combined feed
rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")

ET.SubElement(channel, "title").text = "Woodbridge Community Information"
ET.SubElement(channel, "link").text = (
    "https://woodbridgetv.github.io/woodbridge-weather-rss/"
)
ET.SubElement(channel, "description").text = (
    "Woodbridge weather forecast and New Jersey history"
)
ET.SubElement(channel, "language").text = "en-us"

# Copy all weather items
for item in weather_channel.findall("item"):
    channel.append(deepcopy(item))

# Retrieve today's New Jersey history feed
with urlopen(HISTORY_FEED_URL, timeout=20) as response:
    history_data = response.read()

history_root = ET.fromstring(history_data)
history_channel = history_root.find("channel")

if history_channel is None:
    raise ValueError("History RSS feed has no channel.")

history_items = history_channel.findall("item")

if not history_items:
    raise ValueError("History RSS feed contains no items.")

# Add the history items after the weather items
for item in history_items:
    channel.append(deepcopy(item))

# Save the combined feed
Path("docs").mkdir(exist_ok=True)

ET.ElementTree(rss).write(
    OUTPUT_FILE,
    encoding="utf-8",
    xml_declaration=True
)

print(
    f"Combined feed generated with "
    f"{len(weather_channel.findall('item'))} weather items "
    f"and {len(history_items)} history items."
)
