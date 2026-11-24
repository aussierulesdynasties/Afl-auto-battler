"""Microsoft's Global ML Building Footprints (ODbL) for the land: fetches the Australia tile round Lyndoch
(quadkey 311220301 of the 2026-02-03 release) and keeps the footprints within the land's square, into
work/msbuildings.geojsonl. land.ms_buildings adds the ones OpenStreetMap lacks."""
import csv
import gzip
import io
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import land  # noqa: E402

INDEX = "https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv"
QUADKEY = "311220301"


def main():
    rows = csv.reader(io.StringIO(urllib.request.urlopen(INDEX).read().decode()))
    url = next(r[2] for r in rows if len(r) > 2 and r[0] == "Australia" and r[1] == QUADKEY)
    raw = gzip.decompress(urllib.request.urlopen(url).read()).decode()
    n = 0
    with open(os.path.join(HERE, "work", "msbuildings.geojsonl"), "w") as out:
        for line in raw.splitlines():
            f = json.loads(line)
            c = f["geometry"]["coordinates"][0]
            lon, lat = sum(p[0] for p in c) / len(c), sum(p[1] for p in c) / len(c)
            e, nn = land.en(lat, lon)
            if abs(e) < land.R and abs(nn) < land.R:
                out.write(json.dumps(f) + "\n")
                n += 1
    print("footprints kept", n)


if __name__ == "__main__":
    main()
