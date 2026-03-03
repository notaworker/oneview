#!/usr/bin/env python3
"""
HPE OneView version tracker.
Primary source: GitHub API (HewlettPackard/POSH-HPEOneView releases)
Fallback source: HPE Synergy What's New page (HTML scrape)
"""
import datetime
import re
import requests
from bs4 import BeautifulSoup

RSS_FILE = "oneview.xml"

GITHUB_API = "https://api.github.com/repos/HewlettPackard/POSH-HPEOneView/releases"
FALLBACK_URL = "https://support.hpe.com/docs/display/public/synergy-sw-release/Whats_New.html"

# Matches any X.YY or X.Y version — no hardcoded major version ceiling
VERSION_REGEX = re.compile(r"\b(\d{1,2}\.\d{1,2}(?:\.\d{1,2})?)\b")

# Matches "January 26, 2026" style dates
DATE_REGEX = re.compile(
    r"(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+(\d{1,2}),\s+(\d{4})"
)

def version_key(v: str) -> tuple:
    """Sort versions numerically, supporting X.Y and X.YY.ZZ formats."""
    return tuple(int(x) for x in v.split("."))

def fetch_from_github() -> tuple[str, str | None]:
    """
    Use GitHub Releases API — returns structured JSON with tag + published_at.
    Tag names look like: '9.00.2406.3352', correlating to OneView 9.00, etc.
    """
    headers = {"Accept": "application/vnd.github+json"}
    r = requests.get(GITHUB_API, headers=headers, timeout=15)
    r.raise_for_status()

    releases = r.json()
    if not releases:
        raise RuntimeError("No releases found on GitHub.")

    # Tags look like "9.00.2406.3352" — the first two segments are the OV version
    versions_with_dates = []
    for release in releases:
        tag = release.get("tag_name", "")
        published = release.get("published_at", "")  # ISO 8601, e.g. "2024-10-01T..."
        # Extract major.minor from tag (e.g. "9.00" from "9.00.2406.3352")
        match = re.match(r"^(\d{1,2}\.\d{2})", tag.lstrip("v"))
        if match:
            ov_version = match.group(1)
            date_str = published[:10] if published else None  # "YYYY-MM-DD"
            versions_with_dates.append((ov_version, date_str))

    if not versions_with_dates:
        raise RuntimeError("Could not parse any OneView versions from GitHub tags.")

    latest_version, latest_date = sorted(
        versions_with_dates, key=lambda x: version_key(x[0]), reverse=True
    )[0]

    return latest_version, latest_date

def fetch_from_fallback() -> tuple[str, str | None]:
    """Scrape HPE What's New page as a fallback."""
    r = requests.get(FALLBACK_URL, timeout=40)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    versions = VERSION_REGEX.findall(text)
    if not versions:
        raise RuntimeError("No versions found on fallback page.")

    # Filter to plausible OV versions only (between 6.x and 99.x)
    versions = [v for v in versions if 6 <= int(v.split(".")[0]) <= 99]
    latest_version = sorted(set(versions), key=version_key, reverse=True)[0]

    # Try to find the date closest to the latest version mention
    release_date = None
    dates = DATE_REGEX.findall(text)
    if dates:
        month, day, year = dates[0]
        release_date = f"{year}-{datetime.datetime.strptime(month, '%B').month:02d}-{int(day):02d}"

    return latest_version, release_date

def fetch_latest() -> tuple[str, str | None]:
    """Try GitHub first, fall back to HTML scraping."""
    try:
        version, date = fetch_from_github()
        print(f"[GitHub] Version: {version}, Date: {date}")
        return version, date
    except Exception as e:
        print(f"[GitHub] Failed: {e}. Trying fallback...")

    version, date = fetch_from_fallback()
    print(f"[Fallback] Version: {version}, Date: {date}")
    return version, date

def generate_rss(version: str, release_date: str | None) -> None:
    now = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    pubdate = release_date or "Unknown release date"

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>HPE OneView Latest Version</title>
  <link>https://www.hpe.com</link>
  <description>Daily feed of the newest HPE OneView release.</description>
  <lastBuildDate>{now}</lastBuildDate>
  <item>
    <title>HPE OneView {version}</title>
    <description>Latest HPE OneView version: {version}. Release date: {pubdate}.</description>
    <link>https://github.com/HewlettPackard/POSH-HPEOneView/releases</link>
    <guid isPermaLink="false">oneview-{version}</guid>
    <pubDate>{now}</pubDate>
  </item>
</channel>
</rss>
"""
    with open(RSS_FILE, "w") as f:
        f.write(rss)
    print(f"RSS written to {RSS_FILE}")

def main() -> None:
    version, release_date = fetch_latest()
    print(f"Latest OneView version: {version} (released: {release_date})")
    generate_rss(version, release_date)

if __name__ == "__main__":
    main()
