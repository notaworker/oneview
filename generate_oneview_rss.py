#!/usr/bin/env python3
import datetime
import requests
import re
from bs4 import BeautifulSoup

RSS_FILE = "oneview.xml"

# Public sources: both list OneView versions, only the second includes dates
SOURCES = [
    "https://www.hpe.com/psnow/resources/ebooks/a00113372en_us_v9/s_syn_doc-sm_rn.html",

    # Contains explicit release date references for OneView 11.01
    # Example: Synergy Composer2 (HPE OneView) 11.01 appears in this page.
    # Ref turn13search15
    "https://support.hpe.com/docs/display/public/synergy-sw-release/Whats_New.html"
]

# OneView-only version numbers
VERSION_REGEX = re.compile(
    r"\b(11\.\d{2}|10\.\d{1,2}|9\.\d{1,2}|8\.\d{1,2}|7\.\d{1,2}|6\.\d{1,2})\b"
)

# Matches dates like: "January 26, 2026" or "Jan 26, 2026"
DATE_REGEX = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December|"
    r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),\s+(\d{4})"
)


def fetch_latest_version_and_date():
    versions = set()
    release_date = None

    for url in SOURCES:
        try:
            r = requests.get(url, timeout=40)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            text = soup.get_text(" ", strip=True)

            # Extract versions
            found_versions = VERSION_REGEX.findall(text)
            versions.update(found_versions)

            # Only the "What's New" page includes OneView dates reliably
            found_dates = DATE_REGEX.findall(text)
            if found_dates:
                # Use the FIRST valid release date found on this page
                month, day, year = found_dates[0]
                release_date = f"{month} {day}, {year}"

        except Exception:
            pass

    if not versions:
        raise RuntimeError("No OneView versions found.")

    def version_key(v):
        major, minor = v.split(".")
        return int(major), int(minor)

    latest_version = sorted(versions, key=version_key, reverse=True)[0]

    return latest_version, release_date


def generate_rss(version, release_date):
    now = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    if release_date:
        pubdate = release_date
    else:
        pubdate = "Unknown release date"

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>HPE OneView Latest Version</title>
  <link>https://www.hpe.com</link>
  <description>Daily feed of the newest HPE OneView release.</description>
  <lastBuildDate>{now}</lastBuildDate>
  <pubDate>{now}</pubDate>

  <item>
    <title>HPE OneView {version}</title>
    <description>
      Latest detected HPE OneView version: {version}.
      Release date: {pubdate}.
    </description>
    <link>https://www.hpe.com</link>
    <guid>oneview-{version}</guid>
    <pubDate>{now}</pubDate>
  </item>

</channel>
</rss>
"""
    with open(RSS_FILE, "w") as f:
        f.write(rss)


def main():
    version, release_date = fetch_latest_version_and_date()
    print(f"Detected latest OneView version: {version}")
    print(f"Release date: {release_date}")
    generate_rss(version, release_date)


if __name__ == "__main__":
    main()
