#!/usr/bin/env python3
import requests
import re
from bs4 import BeautifulSoup
import os

URL = "https://support.hpe.com/connect/s/product?language=en_US&cep=on&kmpmoid=5410258&tab=manualsAndGuides"
OUTPUT_FILE = "latest_oneview.txt"

def fetch_latest_version():
    r = requests.get(URL, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Look for patterns like "HPE OneView 11.01"
    versions = set()
    for text in soup.stripped_strings:
        matches = re.findall(r"HPE OneView\s+(\d+\.\d+)", text)
        for m in matches:
            versions.add(m)

    if not versions:
        raise Exception("Could not find any OneView versions on the page.")

    # Sort based on numeric version
    def sort_key(v):
        return tuple(map(int, v.split(".")))

    latest = sorted(versions, key=sort_key, reverse=True)[0]
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
