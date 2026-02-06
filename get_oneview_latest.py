#!/usr/bin/env python3
import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

OUTPUT_FILE = "latest_oneview.txt"

# Public, scrapeable sources (no login, no JS)
SOURCES = [
    # PSNow – OneView Documentation Quick Links (lists 11.01 across docs)
    # Ref: turn10search11
    "https://www.hpe.com/psnow/resources/ebooks/a00113372en_us_v9/s_syn_doc-sm_rn.html",

    # HPE Synergy "What's New" (explicitly mentions OneView 11.01)
    # Ref: turn13search15
    "https://support.hpe.com/docs/display/public/synergy-sw-release/Whats_New.html",

    # HPE Synergy Composer2 11.01 release page (shows Version 11.01.00)
    # Ref: turn13search13, turn13search16
    "https://support.hpe.com/connect/s/softwaredetails?language=en_US&softwareId=MTX_b19804771921492fb5e98cda72&tab=releaseNotes",
]

# Match versions like 11.01, 10.2, 9.10, 8.60.02, etc.
VERSION_REGEX = re.compile(r"\b\d{1,2}\.\d{1,2}(?:\.\d{1,2})?\b")

def make_session():
    retry = Retry(
        total=6,                # total retries
        connect=6,
        read=6,
        backoff_factor=1.5,     # exponential backoff: 1.5s, 3s, 4.5s, ...
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    sess = requests.Session()
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    sess.mount("https://", adapter)
    sess.mount("http://", adapter)
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (GitHubActions OneViewChecker; +https://github.com/) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })
    return sess

def scrape_versions(html: str):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    versions = set(VERSION_REGEX.findall(text))
    return versions

def fetch_latest_version():
    sess = make_session()
    all_versions = set()
    errors = []

    for url in SOURCES:
        try:
            resp = sess.get(url, timeout=45)  # longer timeout for hpe.com
            resp.raise_for_status()
            versions = scrape_versions(resp.text)
            if versions:
                all_versions.update(versions)
        except Exception as e:
            errors.append(f"{urlparse(url).netloc}: {e}")
            # small delay before next source
            time.sleep(1.0)

    if not all_versions:
        raise RuntimeError(
            "No versions found from any source. Errors: " + " | ".join(errors)
        )

    # Normalize and sort (e.g., '8.60.02' -> (8,60,2))
    def key(v):
        return tuple(int(x) for x in v.split("."))

    latest = sorted(all_versions, key=key, reverse=True)[0]
    return latest

def main():
    latest_version = fetch_latest_version()

    previous = None
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            previous = f.read().strip()

    if latest_version != previous:
        print(f"New version detected: {latest_version}")
        with open(OUTPUT_FILE, "w") as f:
            f.write(latest_version + "\n")
    else:
        print("No new version.")

if __name__ == "__main__":
    main()
