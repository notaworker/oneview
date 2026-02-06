#!/usr/bin/env python3
import requests
import re
from bs4 import BeautifulSoup
import os

# PUBLIC, STATIC, GLOBALLY ACCESSIBLE PAGE
URL = "https://www.hpe.com/psnow/resources/ebooks/a00113372en_us_v9/s_syn_doc-sm_rn.html"
OUTPUT_FILE = "latest_oneview.txt"

def fetch_latest_version():
    r = requests.get(URL, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    # Matches 11.01, 10.2, 9.10, etc.
    versions = re.findall(r"\b\d{1,2}\.\d{1,2}\b", text)

    if not versions:
        raise Exception("No versions found in parsed HTML")

    def version_key(v):
        major, minor = v.split(".")
        return (int(major), int(minor))

    latest = sorted(versions, key=version_key, reverse=True)[0]
    return latest

def main():
    latest_version = fetch_latest_version()

    old_version = None
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            old_version = f.read().strip()

    if latest_version != old_version:
        print(f"New version detected: {latest_version}")
        with open(OUTPUT_FILE, "w") as f:
            f.write(latest_version + "\n")
    else:
        print("No new version.")

if __name__ == "__main__":
    main()
