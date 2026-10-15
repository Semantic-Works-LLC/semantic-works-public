#!/usr/bin/env python3
"""Builds site/art-data.js: the permanent artworks at each subway station.

Standard library only. Reads the newest copies of the MTA's art catalog and
station list from data/ (see fetch_static.py). The catalog names a station and
its lines in words, so each artwork is matched to the stations with the same
name that share a line with it.

Much of the catalog's text is garbled at the source: it was written in the old
Mac OS character set, then misread twice on its way to publication, so that an
apostrophe arrives as two unrelated characters. repair() reverses that.
"""
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "site" / "art-data.js"
SUBWAY_AGENCIES = {"NYCT", "SIR"}
# Where the catalog spells a word differently from the station list.
SPELLINGS = {"street": "st", "avenue": "av", "ave": "av", "square": "sq", "parkway": "pkwy", "boulevard": "blvd",
             "road": "rd", "place": "pl", "heights": "hts", "center": "ctr", "junction": "jct", "plaza": "plz",
             "and": "", "the": ""}
# Catalog entries whose station has since been renamed, or that name a whole complex.
BY_HAND = {
    "14 St-6 Av and 14 St-7 Av": ["132", "D19", "L02"],
    "Christopher St-Sheridan Sq": ["133"],
    "Central Park North (110 St)": ["227"],
    "Fulton Center": ["418", "229", "A38", "M22"],
    "Newkirk Av": ["D31"],
}


GARBLED = re.compile(r"[\u00c2\u00c3\u00c5\u00cb\u00e2][^\x00-\x7f]{1,2}")
LOST = "\u00ef\u00bf\u00bd"  # a character the MTA's own export had already replaced with "unknown"
THRICE = ("\u00c3\u0192\u00c2\u00b1", "\u00f1")  # one n-tilde that was misread a third time
LEFTOVERS = {"\uf8ff": "\u2019", "\u00a1_s": "\u2019s", "\u201a-": "-"}  # stray bytes that were not Mac OS text


def as_bytes(text):
    """The bytes a Windows program would have read as this text."""
    return b"".join(char.encode("cp1252") if char.encode("cp1252", "ignore") else char.encode("latin-1")
                    for char in text)


def ungarble(match):
    """Undo the two misreadings of one Mac OS character, or leave the text alone if it is not one."""
    text = match.group(0)
    for length in (len(text), 2):
        try:
            return as_bytes(as_bytes(text[:length]).decode("utf-8")).decode("mac_roman") + text[length:]
        except (UnicodeError, ValueError):
            continue
    return text


def lost_quote(match):
    """Guess the quotation mark that stood where a lost character is, from the letters around it."""
    before, after = match.group(1), match.group(2)
    if before.isalnum() and after.isalpha():
        return before + "\u2019"
    return before + ("\u201c" if not before.strip() and after.strip() else "\u201d")


def repair(text):
    text = text.replace(*THRICE)
    for _ in range(2):  # twice, because a match can swallow the start of a garbled character right after it
        text = GARBLED.sub(ungarble, text)
    for odd, fixed in LEFTOVERS.items():
        text = text.replace(odd, fixed)
    return re.sub(f"(.?){LOST}(?=(.?))", lost_quote, text)


def newest(dataset):
    return sorted((HERE / "data" / dataset).glob("*.csv"))[-1]


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_art():
    return [{key: repair(value) for key, value in row.items()} for row in read(newest("art"))]


def words(name):
    """A station name as a set of words, so word order and punctuation do not matter."""
    parts = re.split(r"[^a-z0-9]+", re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", name.lower()))
    return frozenset(SPELLINGS.get(part, part) for part in parts) - {""}


def lines(text):
    return {line for line in re.split(r"[^A-Z0-9]+", text.upper()) if line}


def match(artwork, stations):
    """The ids of the stations an artwork is at: best name match among stations sharing a line."""
    if artwork["Station Name"] in BY_HAND:
        return BY_HAND[artwork["Station Name"]]
    name, served = words(artwork["Station Name"]), lines(artwork["Line"])
    scored = []
    for station in stations:
        score = len(name & station["words"]) / len(name | station["words"])
        if served & station["lines"] and score >= 0.5:
            scored.append((score, station["id"]))
        elif score == 1:  # the lines at a station change; an exact name is enough
            scored.append((0.99, station["id"]))
    best = max((score for score, _ in scored), default=0)
    return [station_id for score, station_id in scored if score == best]


def main():
    stations = [{"id": row["GTFS Stop ID"], "words": words(row["Stop Name"]),
                 "lines": lines(row["Daytime Routes"])} for row in read(newest("stations"))]
    art, unmatched = defaultdict(list), []
    for row in read_art():
        if row["Agency"] not in SUBWAY_AGENCIES:
            continue
        ids = match(row, stations)
        if not ids:
            unmatched.append(f'{row["Station Name"]} ({row["Line"]})')
        for station_id in ids:
            art[station_id].append({
                "title": row["Art Title"], "artist": row["Artist"], "date": row["Art Date"],
                "material": row["Art Material"], "description": row["Art Description"],
                "link": row["Art Image Link"],
            })
    body = json.dumps(art, separators=(",", ":"), ensure_ascii=False, sort_keys=True)
    OUT.write_text("// Generated by build_art.py from the MTA Permanent Art Catalog. Do not edit.\n"
                   f"const ART = {body};\n", encoding="utf-8")
    print(f"Wrote {OUT}: artworks at {len(art)} stations, {OUT.stat().st_size // 1024} KB")
    if unmatched:
        print(f"{len(unmatched)} artworks matched no station:", "; ".join(sorted(set(unmatched))), file=sys.stderr)


if __name__ == "__main__":
    main()
