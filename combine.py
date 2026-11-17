import xml.etree.ElementTree as ET
from pathlib import Path
from copy import deepcopy
from urllib.request import urlopen
from datetime import datetime
from email.utils import format_datetime, parsedate_to_datetime
from zoneinfo import ZoneInfo

WEATHER_FILE = Path("docs/feed.xml")
OUTPUT_FILE = Path("docs/community-feed.xml")
HISTORY_FEED_URL = "https://woodbridgetv.github.io/nj-history-daily/feed.xml"
EASTERN = ZoneInfo("America/New_York")

# Read and validate the weather feed.
weather_tree = ET.parse(WEATHER_FILE)
weather_root = weather_tree.getroot()
if weather_root.tag != "rss" or weather_root.get("version") != "2.0":
    raise ValueError("Weather source is not RSS 2.0.")
weather_channel = weather_root.find("channel")
if weather_channel is None or not weather_channel.findall("item"):
    raise ValueError("Weather RSS feed has no channel or forecast items.")

# Fetch and validate the history feed.
with urlopen(HISTORY_FEED_URL, timeout=20) as response:
    history_data = response.read()
history_root = ET.fromstring(history_data)
if history_root.tag != "rss" or history_root.get("version") != "2.0":
    raise ValueError("History source is not RSS 2.0.")
history_channel = history_root.find("channel")
if history_channel is None:
    raise ValueError("History RSS feed has no channel.")

now = datetime.now(EASTERN)
today = now.date()

# Build the combined feed.
rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")
ET.SubElement(channel, "title").text = "Woodbridge Community Information"
ET.SubElement(channel, "link").text = "https://woodbridgetv.github.io/woodbridge-weather-rss/"
ET.SubElement(channel, "description").text = "Woodbridge weather forecast and New Jersey history"
ET.SubElement(channel, "language").text = "en-us"
ET.SubElement(channel, "lastBuildDate").text = format_datetime(now)

weather_items = weather_channel.findall("item")
for item in weather_items:
    channel.append(deepcopy(item))

# Include only a completed history item explicitly published for today's
# New Jersey calendar date. This prevents yesterday's completed story from
# being carried forward when today's source is still a placeholder.
added_history = 0
for item in history_channel.findall("item"):
    title = item.findtext("title", "").strip()
    description = item.findtext("description", "").strip()
    guid = item.findtext("guid", "").strip()
    pub_date = item.findtext("pubDate", "").strip()
    is_pending = (
        "being researched" in description.lower()
        or "will be added" in description.lower()
        or "#pending-" in guid.lower()
    )
    if is_pending or not pub_date:
        continue
    try:
        published = parsedate_to_datetime(pub_date).astimezone(EASTERN).date()
    except (TypeError, ValueError, OverflowError):
        continue
    if published != today:
        continue
    channel.append(deepcopy(item))
    added_history += 1

Path("docs").mkdir(exist_ok=True)
ET.ElementTree(rss).write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)
print(
    f"Combined feed generated with {len(weather_items)} weather items "
    f"and {added_history} current-day completed history items."
)
