#!/usr/bin/env python3
"""Downloads the MTA's slow-changing subway datasets into data/<dataset>/<timestamp>.<ext>.

Standard library only. Run it whenever a fresh copy is wanted: a dataset whose
content has not changed since the copy already on disk is not saved again.
Give dataset names as arguments to fetch only those.

Left out on purpose, for size: Subway Hourly Ridership (46 million rows) and the
Origin-Destination Ridership Estimate (83 million rows).
"""
import hashlib
import ssl
import sys
import time
import urllib.request
from pathlib import Path

DATA = Path(__file__).parent / "data"
OPEN_DATA = "https://data.ny.gov/api/views/{}/rows.csv?accessType=DOWNLOAD"
TIMESTAMP = "%Y-%m-%dT%H%M%SZ"

# folder name -> data.ny.gov dataset id
DATASETS = {
    "art": "4y8j-9pkd",                     # MTA Permanent Art Catalog
    "stations": "39hk-dx4f",                # MTA Subway Stations
    "stations-and-complexes": "5f5g-n3cz",  # MTA Subway Stations and Complexes
    "station-complexes": "4ta5-wz5s",       # MTA Subway Station Complexes
    "entrances": "i9wp-a4ja",               # MTA Subway Entrances and Exits
    "amenities": "6yjv-fk7g",               # MTA Subway Station Amenities
    "elevator-inventory": "94fv-bak7",      # MTA Subway Elevator and Escalator Asset Inventory
    "elevator-availability": "rc78-7x78",   # MTA NYCT Subway Elevator and Escalator Availability
    "wifi": "pwa9-tmie",                    # MTA Wi-Fi Locations
    "paths": "tdmq-asac",                   # MTA Subway Paths (distances along each line)
    "running-times": "sp9g-mzjh",           # MTA Subway End-to-End Running Times
    "monthly-ridership": "ak4z-sape",       # MTA Subway Station Monthly Ridership
    "trains-delayed": "9zbp-wz3y",          # MTA Subway Trains Delayed
    "delay-incidents": "g937-7k7c",         # MTA Subway Delay-Causing Incidents
    "major-incidents": "ereg-mcvp",         # MTA Subway Major Incidents
    "wait-assessment": "s666-h6b7",         # MTA Subway Wait Assessment
    "on-time-performance": "f6rf-2a3t",     # MTA Subway Terminal On-Time Performance
    "customer-journey": "r7qk-6tcy",        # MTA Subway Customer Journey-Focused Metrics
    "late-trains": "x7nj-r656",             # MTA Subway 4 to 5 Minute Late Arriving Trains
    "failures": "e2qc-xgxs",                # MTA Subway Mean Distance Between Failures
    "alerts-archive": "7kct-peq7",          # MTA Service Alerts: Beginning April 2020
}
SCHEDULE_URL = "https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip"  # timetable, routes, track geometry


def tls_context():
    context = ssl.create_default_context()
    if Path("/etc/ssl/cert.pem").exists():  # python.org builds for macOS ship without any
        context.load_verify_locations("/etc/ssl/cert.pem")
    return context


def digest(path):
    hasher = hashlib.sha1()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            hasher.update(chunk)
    return hasher.digest()


def fetch(name, url, extension, context):
    folder = DATA / name
    folder.mkdir(parents=True, exist_ok=True)
    earlier = sorted(folder.glob("*" + extension))
    target = folder / (time.strftime(TIMESTAMP, time.gmtime()) + extension)
    partial = target.with_suffix(".part")
    with urllib.request.urlopen(url, timeout=120, context=context) as response, partial.open("wb") as handle:
        for chunk in iter(lambda: response.read(1 << 20), b""):
            handle.write(chunk)
    size = partial.stat().st_size // 1024
    if earlier and digest(earlier[-1]) == digest(partial):
        partial.unlink()
        print(f"{name}: unchanged since {earlier[-1].name}", flush=True)
    else:
        partial.rename(target)
        print(f"{name}: saved {target.name}, {size} KB", flush=True)


def main(argv=None):
    wanted = sys.argv[1:] if argv is None else argv
    sources = {name: (OPEN_DATA.format(dataset), ".csv") for name, dataset in DATASETS.items()}
    sources["schedule"] = (SCHEDULE_URL, ".zip")
    context = tls_context()
    for name, (url, extension) in sources.items():
        if wanted and name not in wanted:
            continue
        try:
            fetch(name, url, extension, context)
        except Exception as problem:  # carry on with the other datasets
            print(f"{name}: FAILED, {type(problem).__name__}: {problem}", flush=True)


if __name__ == "__main__":
    main()
