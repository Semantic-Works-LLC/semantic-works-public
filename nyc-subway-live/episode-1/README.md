# Semantic Works: NYC Subway Live — Episode 1 (The Lines and Stations)

A live map of the New York subway that shows the service alerts the MTA publishes, keeps a history of them, and lets you wind the clock back. It was built in one conversation between Pavel and Claude in October 2026, starting from a spoken idea.

**This is an experiment. It is not an official MTA or NYC Subway product.** It is not made, endorsed or checked by the MTA or the NYC Subway, and what it shows may be late or wrong. Do not rely on it for travel.

The conversation that built the app, with Pavel's requests as understood, is in [TRANSCRIPT.md](TRANSCRIPT.md). A slide-by-slide account of the journey, with screenshots of each stage, can be [followed online](https://semantic-works.com/public/nyc-subway-live/episode-1/journey/); the file itself is [journey/index.html](journey/index.html).

## How we started

Pavel had heard that the MTA publishes live updates about closures, and asked for three things in one breath:

1. **A map** of the subway with its stations, drawn in the page.
2. **Live events** on that map, fetched every 30 seconds or so.
3. **History**, with a way to rewind to an earlier moment and return to the present.

Before writing anything, Claude checked what the MTA offers:

- **The alerts feed is free and needs no key.** One address returns every published alert.
- **The map can be drawn from the MTA's own schedule,** which holds the real track geometry and every station's position.
- **History needs a server.** A page alone forgets everything when it is closed, so a small Python program does the fetching and saves what changes.

## What we built

One page and one server.

![The live map with alerts on the lines and stations, and the Events tab open beside it](screenshot.jpg)

- **Map.** All 29 routes and 496 stations in their real positions, with pan, zoom and a fit-to-view button. Stations are filled with their line's colour.
- **Live alerts.** Stations named in an alert get a ring in the alert's colour: suspended, delays, service change or notice. A line with an alert has a pulsing outline in a lighter shade of its own colour.
- **Side panel** that slides in and out, with two tabs:
  - **Events:** the alerts that arrived in the chosen time range, with a count underneath.
  - **Selection:** details of whatever is selected.
- **Selection.** A station shows its alerts, facts from the MTA station list and its artwork as a carousel. A line shows its alerts, the MTA's description and every stop. An event shows its full text and the stations it affects.
- **Timeline** at the top of the Events tab:
  - a slider with two handles, where the right one is the moment shown on the map and the left one narrows the list;
  - a mark for every change, which can be clicked to put the range around it;
  - a menu for how much history the slider covers.
- **Recording.** While it runs, the server saves under `data/`, one folder per feed, each update a file named by its time:
  - alert changes, checked every 30 seconds;
  - train positions and predicted arrivals, every 15 minutes, exactly as received;
  - elevator and escalator outages, when they change.
- **Downloads.** `fetch_static.py` fetches 21 of the MTA's slow-changing datasets and the schedule, about 220 MB.

## How we built it

- **Small steps, checked live.** Pavel spoke each request, Claude changed the page, and the open browser reloaded by itself.
- **Look before building.** Claude downloaded each feed and inspected it before using it. The train feeds were decoded by hand to find out what they hold: which station each train is at and its predicted arrivals, but no GPS position and no speed.
- **Store what changed, not every copy.** The alert history is a log of arrivals and removals, which the page replays up to any moment.
- **Record first.** Train history cannot be downloaded later, because the MTA publishes only the present moment. Recording started before anything was drawn.
- **Features first, no tests.** Nothing here has automated tests.

## Run it

```bash
python3 server.py
```

Then open http://localhost:8001.

The presentation needs no server: open `journey/index.html` in a browser.

The app needs only Python 3 and a browser. It uses no libraries, no API key and no account. The server fetches the MTA's public feeds, so it needs an internet connection; the page itself talks only to the server on your own machine.

Station art is not included in this repository. To add it, download the two datasets it is built from and build it:

```bash
python3 fetch_static.py art stations
python3 build_art.py
```

## What we improved

- **The first screen was an error.** Python on the Mac had no list of trusted certificates and the map area measured as zero. Both were found by opening the page and looking.
- **Pop-up to panel.** Station details began as a card in the corner, then a pop-up attached to the station. Pavel disliked the pop-up, and it became the Selection tab.
- **Timeline, three versions.** A slider along the bottom; then inside the Events tab with bold, clickable marks; then two handles that select a range.
- **Garbled art text.** 253 of the 394 entries in the MTA's art catalog arrive with apostrophes, quotation marks and accents as wrong characters. The text was written in the old Mac character set and misread twice. `build_art.py` reverses that. 95 characters were already lost at the source and were put back by position, which is a guess.
- **Pulsing, six tries.** Moving dashes suggested a direction the data does not have. Flashing the whole line did not read well, and making it wider at the peak looked jittery. The jitter led to a real fault: every 5-second refresh was redrawing the pulsing shapes and restarting each pulse. The final form is a steady line with a pulsing outline.
- **Trains every 15 minutes.** Recording every 30 seconds would have taken about 380 MB a day.

## How we finished

The app works as described above and has no tests.

These are open:

- **Trains are recorded but not drawn.** Putting them on the map, on the same timeline, is the obvious next step.
- **Direction is not shown.** Lines run both ways, and the map does not show which way an alert applies.
- **Speed is not computed.** It has to be worked out from the recordings and the station-to-station distances, which are downloaded but unused.
- **Art has no pictures.** The catalog only links to pages on mta.info. The matching of 309 artworks to stations was spot-checked, not fully checked.
- **Shared tracks show one colour** and select one line. Where several lines run on the same tracks, the one drawn last covers the others.
- **History has gaps** whenever the server is not running.
- **Later episodes are not decided.** Two have been discussed: the rider's view (a route to work) and the operator's view (what the recorded history shows).

## Files

| Path | What it is |
|---|---|
| `server.py` | The web server and recorder: serves `site/`, fetches the MTA feeds, saves history under `data/`, and reloads the page when a file changes |
| `site/index.html` | The app: one page with its HTML, CSS and JavaScript |
| `site/map-data.js` | The lines and stations the page draws. Generated by `build_map.py`; do not edit |
| `site/station-data.js` | Facts about each station. Generated by `build_station_info.py`; do not edit |
| `site/art-data.js` | The artworks at each station. Generated by `build_art.py`; not included in the repository |
| `journey/index.html` | The presentation of how the app was built: one file with its screenshots inside it |
| `screenshot.jpg` | The picture of the app used in this README |
| `fetch_static.py` | Downloads the MTA's slow-changing datasets into `data/` |
| `build_map.py` | Builds `site/map-data.js` from the MTA schedule |
| `build_station_info.py` | Builds `site/station-data.js` from the MTA station list |
| `build_art.py` | Builds `site/art-data.js` from the MTA art catalog, repairing its text |
| `data/` | Everything downloaded and recorded. Created when the scripts run; not included in the repository |
| `TRANSCRIPT.md` | The conversation record |

## Data

All data comes from the Metropolitan Transportation Authority's public feeds and open datasets. The map and station files in `site/` are derived from them. The MTA's names, line colours and route symbols belong to the MTA.
