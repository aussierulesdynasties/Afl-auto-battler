"""Fit the 3D crowd's attendance model to real AFL crowds (2023-2026) and write
data/attendance.json. Looks only: the match sim never reads it.

Input: data/raw/attendance_2023_2026.csv, every home-and-away match and final of
2023-2026 with its crowd, parsed from AFL Tables' season pages
(afltables.com/afl/seas/<year>.html) by tools/attendance/parse_afltables.py.

The model (log crowd, least squares with a light ridge):
  log(att) = venue + home club's pull + away club's pull
             + derby (both clubs from the ground's state) / neutral ground
             + kickoff slot (day, twilight, night) + finals week
and a fixture is capped at its ground's capacity. The spread of the real crowds
round the model (sd of the log residual) gives each fixture its own swing.
"""
import csv, json, math, sys
import numpy as np

ROOT = __file__.rsplit("/tools/", 1)[0]
SRC = ROOT + "/data/raw/attendance_2023_2026.csv"
OUT = ROOT + "/data/attendance.json"

# AFL Tables' names -> the game's (data/clubs.csv codes; data/grounds.json names).
CLUB = {"Adelaide": "ADE", "Brisbane Lions": "BRL", "Carlton": "CAR", "Collingwood": "COL",
        "Essendon": "ESS", "Fremantle": "FRE", "Geelong": "GEE", "Gold Coast": "GCS",
        "Greater Western Sydney": "GWS", "Hawthorn": "HAW", "Melbourne": "MEL",
        "North Melbourne": "NTH", "Port Adelaide": "PAD", "Richmond": "RIC", "St Kilda": "STK",
        "Sydney": "SYD", "West Coast": "WCE", "Western Bulldogs": "WBD"}
VENUE = {"M.C.G.": "MCG", "Docklands": "Marvel Stadium", "Adelaide Oval": "Adelaide Oval",
         "Perth Stadium": "Optus Stadium", "Gabba": "The Gabba", "S.C.G.": "SCG",
         "Kardinia Park": "GMHBA Stadium", "Carrara": "People First Stadium",
         "Sydney Showground": "Engie Stadium", "York Park": "York Park",
         "Bellerive Oval": "Bellerive Oval", "Manuka Oval": "Manuka Oval",
         "Norwood Oval": "Norwood Oval", "Marrara Oval": "Marrara Oval",
         "Eureka Stadium": "Mars Stadium", "Traeger Park": "Traeger Park",
         "Summit Sports Park": "Summit Park", "Barossa Park": "Barossa Park",
         "Hands Oval": "Hands Oval"}
CLUB_STATE = {"ADE": "SA", "PAD": "SA", "BRL": "QLD", "GCS": "QLD", "GWS": "NSW", "SYD": "NSW",
              "FRE": "WA", "WCE": "WA", "TAS": "TAS", "CANB": "ACT"}  # every other club VIC
# Every ground the game draws, its state and its published capacity (seats plus standing room,
# as each ground states it; the 1990s grounds as they were then). Sources: austadiums.com and
# each ground's own page, checked 2026-11; a crowd above the figure raises it (MCG Grand Finals).
GROUND = {
    "MCG": ("VIC", 100024), "Marvel Stadium": ("VIC", 53359), "Adelaide Oval": ("SA", 53583),
    "Optus Stadium": ("WA", 61266), "The Gabba": ("QLD", 39000), "SCG": ("NSW", 48000),
    "GMHBA Stadium": ("VIC", 40000), "People First Stadium": ("QLD", 22000),
    "Engie Stadium": ("NSW", 23500), "Bellerive Oval": ("TAS", 19500), "Manuka Oval": ("ACT", 13550),
    "Norwood Oval": ("SA", 10000), "Barossa Park": ("SA", 10000), "York Park": ("TAS", 19000),
    "Marrara Oval": ("NT", 12500), "Mars Stadium": ("VIC", 11000), "Traeger Park": ("NT", 10000),
    "Cazaly's Stadium": ("QLD", 13500), "Riverway Stadium": ("QLD", 10000),
    "Summit Park": ("WA", 10000), "Hands Oval": ("WA", 10000), "Accor Stadium": ("NSW", 83500),
    "Macquarie Point Stadium": ("TAS", 23000), "North Hobart Oval": ("TAS", 15000),
    "Bruce Stadium": ("ACT", 25000), "Blacktown International Sportspark": ("NSW", 10000),
    "Sky Stadium": ("NZ", 34500), "Jiangwan Stadium": ("CN", 10000),
    "Waverley Park": ("VIC", 72000), "Victoria Park": ("VIC", 30000), "Windy Hill": ("VIC", 30000),
    "Moorabbin Oval": ("VIC", 30000), "Ikon Park": ("VIC", 35000), "Whitten Oval": ("VIC", 25000),
    "Football Park": ("SA", 51240), "Subiaco Oval": ("WA", 43500), "WACA": ("WA", 24500),
}
SLOTS = ["day", "twilight", "night"]
FINALS = ["Qualifying Final", "Elimination Final", "Semi Final", "Preliminary Final", "Grand Final"]
RIDGE = 1.0


def slot_of(when):
    # "Fri 07-Mar-2025 7:40 PM (6:40 PM)": the ground's own clock comes first.
    parts = when.split()
    h, m = parts[2].split(":")
    h = int(h) % 12 + (12 if parts[3] == "PM" else 0)
    return "day" if h < 16 else ("twilight" if h < 18 else "night")


def club_state(c):
    return CLUB_STATE.get(c, "VIC")


def main():
    rows = list(csv.DictReader(open(SRC)))
    games = []
    for r in rows:
        v = VENUE[r["venue"]]
        h, a = CLUB[r["home"]], CLUB[r["away"]]
        fin = r["round"] if r["round"] in FINALS else ""
        games.append(dict(v=v, h=h, a=a, slot=slot_of(r["when"]), fin=fin, att=int(r["att"])))
    venues = sorted({g["v"] for g in games})
    clubs = sorted(CLUB.values())
    cols = (["v:" + v for v in venues] + ["h:" + c for c in clubs] + ["a:" + c for c in clubs]
            + ["derby", "neutral", "slot:twilight", "slot:night"] + ["fin:" + f for f in FINALS])
    ix = {c: i for i, c in enumerate(cols)}
    X = np.zeros((len(games), len(cols)))
    y = np.zeros(len(games))
    for i, g in enumerate(games):
        st = GROUND[g["v"]][0]
        X[i, ix["v:" + g["v"]]] = 1
        X[i, ix["h:" + g["h"]]] = 1
        X[i, ix["a:" + g["a"]]] = 1
        hs, as_ = club_state(g["h"]) == st, club_state(g["a"]) == st
        if hs and as_:
            X[i, ix["derby"]] = 1
        if not hs and not as_:
            X[i, ix["neutral"]] = 1
        if g["slot"] != "day":
            X[i, ix["slot:" + g["slot"]]] = 1
        if g["fin"]:
            X[i, ix["fin:" + g["fin"]]] = 1
        y[i] = math.log(g["att"])
    # Ridge on the club pulls only (a venue, derby, slot or finals week is its own mean); club pulls are
    # centred afterwards into the venues so an average club adds nothing.
    pen = np.array([RIDGE if c[:2] in ("h:", "a:") else 0.0 for c in cols])
    beta = np.linalg.solve(X.T @ X + np.diag(pen), X.T @ y)
    b = dict(zip(cols, beta))
    hmean = np.mean([b["h:" + c] for c in clubs])
    amean = np.mean([b["a:" + c] for c in clubs])
    resid = y - X @ beta
    sd = float(np.std(resid))
    out = {
        "_about": ("How many people come to each match, for the 3D crowd (looks only: the match sim "
                   "never reads this). Fitted by tools/attendance/fit.py to every AFL crowd of "
                   "2023-2026 (data/raw/attendance_2023_2026.csv, from AFL Tables): "
                   "crowd = exp(venue + home pull + away pull + derby/neutral + slot + finals + swing), "
                   "capped at the ground's capacity; swing is normal with sd 'swing_sd', seeded by the "
                   "match. A ground with no crowds of its own draws as a known ground of its size does: log crowd = fallback[0] + fallback[1] x log capacity; a Grand Final sells out. "
                   "Do not edit by hand."),
        "games": len(games),
        "swing_sd": round(sd, 4),
        "venue": {v: round(float(b["v:" + v] + hmean + amean), 4) for v in venues},
        "home": {c: round(float(b["h:" + c] - hmean), 4) for c in clubs},
        "away": {c: round(float(b["a:" + c] - amean), 4) for c in clubs},
        "derby": round(float(b["derby"]), 4),
        "neutral": round(float(b["neutral"]), 4),
        "slot": {"day": 0.0, "twilight": round(float(b["slot:twilight"]), 4),
                 "night": round(float(b["slot:night"]), 4)},
        "finals": {f: round(float(b["fin:" + f]), 4) for f in FINALS},
        "fallback": [0.0, 1.0],
        "capacity": {k: v[1] for k, v in GROUND.items()},
        "state": {k: v[0] for k, v in GROUND.items()},
        "club_state": CLUB_STATE,
    }
    # Capacity: never below the biggest crowd a ground really held.
    for g in games:
        out["capacity"][g["v"]] = max(out["capacity"][g["v"]], g["att"])
    # A ground with no crowds of its own: the share of its capacity a known ground of its size
    # draws (log mean crowd on log capacity across the known grounds: the big ones fill less).
    lc = np.array([math.log(out["capacity"][v]) for v in venues])
    lm = np.array([math.log(np.mean([g["att"] for g in games if g["v"] == v])) for v in venues])
    slope, icept = np.polyfit(lc, lm, 1)
    out["fallback"] = [round(float(icept), 4), round(float(slope), 4)]
    json.dump(out, open(OUT, "w"), indent=1)
    # The report: real v model by ground, and the worst fits.
    pred = X @ beta
    print("games", len(games), "residual sd (log)", round(sd, 3))
    print("%-22s %5s %8s %8s %8s" % ("ground", "n", "real", "model", "cap"))
    for v in venues:
        sel = [i for i, g in enumerate(games) if g["v"] == v]
        real = np.mean([games[i]["att"] for i in sel])
        mod = np.mean([min(math.exp(pred[i] + sd * sd / 2), out["capacity"][v]) for i in sel])
        print("%-22s %5d %8.0f %8.0f %8d" % (v, len(sel), real, mod, out["capacity"][v]))
    print("home pull", {k: round(v, 2) for k, v in sorted(out["home"].items(), key=lambda x: -x[1])})
    print("away pull", {k: round(v, 2) for k, v in sorted(out["away"].items(), key=lambda x: -x[1])})
    print("derby", out["derby"], "neutral", out["neutral"], "slot", out["slot"], "finals", out["finals"])


if __name__ == "__main__":
    main()
