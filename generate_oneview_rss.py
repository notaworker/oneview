#!/usr/bin/env python3
import datetime
import requests
import re
from bs4 import BeautifulSoup

RSS_FILE = "oneview.xml"

SOURCES = [
    # OneView docs page listing 11.01
    "https://www.hpe.com/psnow/resources/ebooks/a00113372en_us_v9/s_syn_doc-sm_rn.html",
    # Synergy "What's New" page that explicitly lists OneView 11.01
    "https://support.hpe.com/docs/display/public/synergy-sw-release/Whats_New.html"
]

# Strict OneView-only version patterns
VERSION_REGEX = re.compile(
    r"\b(11\.\d{2}|10\.\d{1,2}|9\.\d{1,2}|8\.\d{1,2}|7\.\d{1,2}|6\.\d{1,2})\b"
)

def fetch_latest_version():
    versions = set()
    for url in SOURCES:
        try:
            r = requests.get(url, timeout=40)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            text = soup.get_text(" ", strip=True)
            found = VERSION_REGEX.findall(text)
            versions.update(found)
        except Exception:
            pass

    if not versions:
        raise RuntimeError("No OneView versions found.")

    def version_key(v):
        major, minor = v.split(".")
        return int(major), int(minor)

    return sorted(versions, key=version_key, reverse=True)[0]

def generate_rss(latest_version):
    now = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>HPE OneView Latest Version</title>
  <link>https://www.hpe.com</link>
  <description>Daily feed of the newest HPE OneView release.</description>
  <lastBuildDate>{now}</lastBuildDate>
  <pubDate>{now}</pubDate>

  <item>
    <title>HPE OneView {latest_version}</title>
    <description>Latest detected HPE OneView version: {latest_version}</description>
    <link>https://www.hpe.com</link>
    <guid>oneview-{latest_version}</guid>
    <pubDate>{now}</pubDate>
  </item>

</channel>
</rss>
"""
    with open(RSS_FILE, "w") as f:
        f.write(rss)

def main():
    latest = fetch_latest_version()
    print(f"Detected latest OneView version: {latest}")
    generate_rss(latest)

if __name__ == "__main__":
    main()
``
