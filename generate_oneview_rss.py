#!/usr/bin/env python3
"""
HPE OneView version tracker.
- Version:  Parsed from the HPE Synergy Overview table (index.html)
            The first "Recommended" row is always the latest version.
- Date:     Scraped from What's New headings (e.g. "★HPE Synergy Composer2 (HPE OneView) 11.1")
            No dates are published on either page, so pubDate falls back to today's date.
"""
import datetime
import re
import requests
from bs4 import BeautifulSoup

RSS_FILE = "oneview.xml"

# Primary: structured version table — top row = latest recommended version
OVERVIEW_URL = "https://support.hpe.com/docs/display/public/synergy-sw-release/index.html"
# Secondary: used only to confirm version exists as a named release
WHATSNEW_URL = "https://support.hpe.com/docs/display/public/synergy-sw-release/Whats_New.html"

# Matches "OneView) 11.1" or "OneView) 11.01" in headings
OV_HEADING_REGEX = re.compile(r"OneView\)\s*(\d+\.\d+)", re.IGNORECASE)
# Generic version in table cells: "11.1", "10.2" etc.
OV_TABLE_REGEX = re.compile(r"\bOneView\)\s*(\d+\.\d+)", re.IGNORECASE)

def version_key(v: str) -> tuple:
    return tuple(int(x) for x in v.split("."))

def fetch_latest_from_overview() -> str:
    """
    Parse the overview table. The first linked version under
    'Recommended for latest fixes and features' is always the latest.
    """
    r = requests.get(OVERVIEW_URL, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Find all links whose text matches "Composer (HPE OneView) X.Y"
    versions = []
    for a in soup.find_all("a"):
        text = a.get_text(strip=True)
        m = OV_TABLE_REGEX.search(text)
        if m:
            versions.append(m.group(1))

    if not versions:
        raise RuntimeError("No OneView versions found in overview table.")

    # The table is ordered newest→oldest, so first entry = latest
    # But also sort as a safety net in case page structure shifts
    return sorted(set(versions), key=version_key, reverse=True)[0]

def fetch_latest_from_whatsnew() -> str:
    """Fallback: scrape version from What's New headings."""
    r = requests.get(WHATSNEW_URL, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    versions = []
    for heading in soup.find_all(["h1", "h2", "h3"]):
        m = OV_HEADING_REGEX.search(heading.get_text())
        if m:
            versions.append(m.group(1))

    if not versions:
        raise RuntimeError("No OneView versions found in What's New page.")

    return sorted(set(versions), key=version_key, reverse=True)[0]

def fetch_latest() -> tuple[str, str]:
    """Returns (version, iso_date). Date is always today — HPE doesn't publish it."""
    try:
        version = fetch_latest_from_overview()
        print(f"[Overview] Latest version: {version}")
    except Exception as e:
        print(f"[Overview] Failed ({e}), trying What's New fallback...")
        version = fetch_latest_from_whatsnew()
        print(f"[Whats_New] Latest version: {version}")

    # HPE does not publish a machine-readable release date on these pages
    today = datetime.date.today().isoformat()
    return version, today

def generate_rss(version: str, check_date: str) -> None:
    now_rfc = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>HPE OneView Latest Version</title>
  <link>{OVERVIEW_URL}</link>
  <description>Daily feed of the newest HPE OneView release.</description>
  <lastBuildDate>{now_rfc}</lastBuildDate>
  <item>
    <title>HPE OneView {version}</title>
    <description>Latest HPE OneView version: {version} (detected on {check_date}).</description>
    <link>{OVERVIEW_URL}</link>
    <guid isPermaLink="false">oneview-{version}</guid>
    <pubDate>{now_rfc}</pubDate>
  </item>
</channel>
</rss>
"""
    with open(RSS_FILE, "w") as f:
        f.write(rss)
    print(f"RSS written to {RSS_FILE}")

def main() -> None:
    version, check_date = fetch_latest()
    print(f"Latest HPE OneView: {version} (checked: {check_date})")
    generate_rss(version, check_date)

if __name__ == "__main__":
    main()
