# SANFL scrape (stage A). Reads the sanflstats.com API json (src_sanfl/), the club guide rosters (rosters.json from rows.py + parse.py) and team-sheet entries, and writes sanfl_players_2026.csv, sanfl_afl_listed_2026.csv and sanfl_clubs_2026.csv (copied into ../staging/). The downloads are not in the repo.
# Kept as the record of how tools/state_leagues/staging/ was made; tools/state_leagues/build.py
# rebuilds data/state_leagues/ from staging/ without them.
import json, csv, re, os, glob, sys
from collections import Counter, defaultdict

ROOT = "C:/kt/state_leagues"
SRC = ROOT + "/src_sanfl"
REPO = "C:/Users/DANTE/Documents/GitHub/Afl-auto-battler"
API = "https://api3.sanflstats.com"

CLUBS = [
    # id, name, short, sanfl teamCode, guide key, guide pdf, club page slug, kind, afl
    ("ADR", "Adelaide", "Crows", "ADL", "Adelaide", "2026/03/20151754/Adelaide-Club-Guide-Mar-19-2026.pdf", "adelaide", "reserves", "ADE"),
    ("CTD", "Central District", "Bulldogs", "CNTRL", "Central", "2026/03/20151627/Central-Club-Guide-Mar-19-2026.pdf", "central-district", "standalone", ""),
    ("GLG", "Glenelg", "Tigers", "TIGERS", "Glenelg", "2026/03/19094953/Glenelg-Club-Guide-Mar-18-2026.pdf", "glenelg", "standalone", ""),
    ("NAD", "North Adelaide", "Roosters", "NORTH", "North", "2026/03/19094538/North-Club-Guide-Mar-18-2026.pdf", "north-adelaide", "standalone", ""),
    ("NWD", "Norwood", "Redlegs", "NWD", "Norwood", "2026/03/19094230/Norwood-Club-Guide-Mar-18-2026.pdf", "norwood", "standalone", ""),
    ("PAM", "Port Adelaide", "Magpies", "PORT", "Port", "2026/03/20151711/Port-Club-Guide-Mar-19-2026.pdf", "port-adelaide", "reserves", "PAD"),
    ("SAD", "South Adelaide", "Panthers", "SOUTH", "South", "2026/03/19094742/South-Club-Guide-Mar-18-2026.pdf", "south-adelaide", "standalone", ""),
    ("STU", "Sturt", "Double Blues", "STURT", "Sturt", "2026/03/19095043/Sturt-Club-Guide-Mar-18-2026.pdf", "sturt", "standalone", ""),
    ("WAD", "West Adelaide", "Bloods", "WEST", "West", "2026/03/19094504/West-Club-Guide-Mar-18-2026.pdf", "west-adelaide", "standalone", ""),
    ("WWT", "Woodville-West Torrens", "Eagles", "EAGLES", "Eagles", "2026/03/19094615/Eagles-Club-Guide-Mar-18-2026.pdf", "woodville-west-torrens", "standalone", ""),
]
# Home grounds: sanfl.com.au club pages (Adelaide page says n/a).
GROUNDS = {"ADR": "", "CTD": "X Convenience Oval", "GLG": "Stratarama Stadium", "NAD": "Revo Fitness Oval",
           "NWD": "Coopers Stadium", "PAM": "Alberton Oval", "SAD": "Magain Stadium", "STU": "Thomas Farms Oval",
           "WAD": "Richmond Oval", "WWT": "Maughan Thiem Kia Oval"}
# Colours: Wikipedia club infobox colour boxes (hex where the infobox gives one).
COLOURS = {
    "ADR": ("#0F1432", "#FF001E", "#FFAA00", "Adelaide_Football_Club"),
    "CTD": ("", "", "", ""),
    "GLG": ("#010101", "#FEBC03", "", "Glenelg_Football_Club"),
    "NAD": ("#E3030F", "#FFFFFF", "", "North_Adelaide_Football_Club"),
    "NWD": ("#001448", "#EE0F49", "", "Norwood_Football_Club"),
    "PAM": ("#000000", "#FFFFFF", "", "Port_Adelaide_Football_Club"),
    "SAD": ("#021637", "#FFFFFF", "", "South_Adelaide_Football_Club"),
    "STU": ("#6CACE4", "#041E42", "", "Sturt_Football_Club"),
    "WAD": ("#000000", "#ED174B", "", "West_Adelaide_Football_Club"),
    "WWT": ("#002A62", "#00553D", "#FFD400", "Woodville-West_Torrens_Football_Club"),
}
BY_CODE = {c[3]: c for c in CLUBS}

def norm(s):
    return re.sub(r"[^a-z]", "", (s or "").lower())

def iso(d):
    if not d:
        return ""
    m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$", d.strip())
    return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}" if m else ""

# ---- clubs file
os.makedirs(ROOT, exist_ok=True)
with open(ROOT + "/sanfl_clubs_2026.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["code", "name", "short", "league", "kind", "afl_club", "ground", "primary", "secondary", "accent", "sanfl_team_code", "src", "colour_src"])
    for cid, name, short, tc, gk, pdf, slug, kind, afl in CLUBS:
        p, s2, a, wk = COLOURS[cid]
        w.writerow([cid, name, short, "SANFL", kind, afl, GROUNDS[cid], p, s2, a, tc,
                    f"https://sanfl.com.au/league/clubs/{slug}/",
                    f"https://en.wikipedia.org/wiki/{wk}" if wk else ""])

# ---- AFL lists
afl = list(csv.DictReader(open(REPO + "/data/players_enriched_2026.csv", encoding="utf-8")))
for r in afl:
    r["_src"] = "players_2026.csv"
adds = list(csv.DictReader(open(REPO + "/data/list_additions_2026.csv", encoding="utf-8")))
for r in adds:
    r["num"] = ""
    r["_src"] = "list_additions_2026.csv"
afl = afl + adds
afl_by_dob_last = {(r["dob"], norm(r["last"])): r for r in afl if r.get("dob")}
afl_by_name = defaultdict(list)
for r in afl:
    afl_by_name[(r["club"], norm(r["first"]), norm(r["last"]))].append(r)

def afl_link(first, last, dob, sanfl_tc):
    r = afl_by_dob_last.get((dob, norm(last)))
    if r:
        return r
    c = BY_CODE[sanfl_tc][8]
    if c:
        hits = afl_by_name.get((c, norm(first), norm(last)))
        if hits and len(hits) == 1:
            return hits[0]
    return None

# ---- guide rosters
guide = json.load(open(ROOT + "/work/rosters.json"))

# ---- API squads + details
squads = {}
for cid, name, short, tc, *_ in CLUBS:
    squads[tc] = json.load(open(f"{SRC}/api/players_{tc}.json"))["players"]

def detail(pid):
    fp = f"{SRC}/api/players/{pid}.json"
    if not os.path.exists(fp) or os.path.getsize(fp) < 50:
        return None
    try:
        d = json.load(open(fp, encoding="utf-8"))
    except Exception:
        return None
    return d["players"][0] if d.get("players") else None

STAT = [("gm", "matchesPlayed"), ("gl", "goals"), ("bh", "behinds"), ("di", "disposals"), ("ki", "kicks"),
        ("hb", "handballs"), ("mk", "marks"), ("cm", "marksContested"), ("tk", "tackles"), ("ho", "hitouts"),
        ("cl", "clearances"), ("if50", "inside50s"), ("rb", "rebound50s"), ("ff", "freesFor"), ("fa", "freesAgainst")]

def season_stats(p, league):
    out = {}
    for c in (p or {}).get("careerStats") or []:
        if str(c.get("season")) == "2026" and c.get("leagueCode") == league:
            for k, src in STAT:
                v = c.get(src)
                if v not in (None, ""):
                    out[k] = out.get(k, 0) + int(float(v))
    if not out and league == "sanfl":
        cs = (p or {}).get("currentSeasonStats") or {}
        if str(cs.get("season")) == "2026" and cs.get("leagueCode") == league:
            for k, src in STAT:
                v = cs.get(src)
                if v not in (None, ""):
                    out[k] = int(float(v))
    return out

# ---- team sheet positions
entries = json.load(open(ROOT + "/work/sheet_entries.json"))

# ---- assemble players: API squad first, then guide-only rows
players = []
for cid, name, short, tc, gk, pdf, slug, kind, aflc in CLUBS:
    groster = guide[gk]
    used_g = set()
    for sp in squads[tc]:
        first, last = sp.get("firstname", "").strip(), sp.get("surname", "").strip()
        dob = iso(sp.get("dob", ""))
        g = None
        for i, gr in enumerate(groster):
            if i in used_g:
                continue
            if (dob and iso(gr["DOB"]) == dob and norm(gr["Last"]) == norm(last)) or \
               (norm(gr["Last"]) == norm(last) and norm(gr["First"]) == norm(first)):
                g = gr; used_g.add(i); break
        pid = sp.get("playerId", "")
        d = detail(pid) if pid else None
        if g:
            first, last = g["First"], g["Last"]
        else:
            last = re.sub(r"^(Mc|O'|D')([a-z])", lambda m: m.group(1) + m.group(2).upper(), last)
        players.append({"cid": cid, "tc": tc, "pid": pid, "first": first, "last": last,
                        "num": sp.get("jumperNumber", "") or (g or {}).get("#", ""),
                        "dob": dob or iso((g or {}).get("DOB", "")),
                        "height_cm": sp.get("height", "") or (g or {}).get("Cm", ""),
                        "weight_kg": (d or {}).get("weight", "") or "",
                        "career_gm": (g or {}).get("L Gm", ""), "career_gl": (g or {}).get("L Gl", ""),
                        "guide_afl": (g or {}).get("AFL", ""),
                        "in_guide": bool(g), "in_api": True, "d": d, "pdf": pdf})
    for i, gr in enumerate(groster):
        if i in used_g:
            continue
        players.append({"cid": cid, "tc": tc, "pid": "", "first": gr["First"], "last": gr["Last"],
                        "num": gr.get("#", ""), "dob": iso(gr["DOB"]), "height_cm": gr.get("Cm", ""),
                        "weight_kg": "", "career_gm": gr.get("L Gm", ""), "career_gl": gr.get("L Gl", ""),
                        "guide_afl": gr.get("AFL", ""), "in_guide": True, "in_api": False, "d": None, "pdf": pdf})

# dedupe API duplicates (same pid listed twice in a squad)
seen = set(); dedup = []
for p in players:
    k = (p["cid"], p["pid"] or (p["first"], p["last"], p["dob"]))
    if k in seen:
        continue
    seen.add(k); dedup.append(p)
players = dedup
# merge a no-id row into an id row of the same club, surname and jumper number (e.g. Nic / Nicholas)
merged = []
for p in players:
    if not p["pid"]:
        twin = [q for q in players if q is not p and q["pid"] and q["cid"] == p["cid"]
                and norm(q["last"]) == norm(p["last"]) and str(q["num"]) == str(p["num"])
                and norm(q["first"])[:1] == norm(p["first"])[:1]]
        if len(twin) == 1:
            q = twin[0]
            for k in ("dob", "height_cm", "career_gm", "career_gl", "guide_afl"):
                if not q.get(k) and p.get(k):
                    q[k] = p[k]
            q["in_guide"] = q["in_guide"] or p["in_guide"]
            continue
    merged.append(p)
players = merged

# positions: match sheet names to players
by_club_full = defaultdict(list); by_club_last = defaultdict(list); by_full = defaultdict(list)
for p in players:
    by_club_full[(p["tc"], norm(p["first"]) + norm(p["last"]))].append(p)
    by_club_last[(p["tc"], norm(p["last"]))].append(p)
    by_full[norm(p["first"]) + norm(p["last"])].append(p)
unmatched = Counter()
for e in entries:
    parts = e["name"].split(" ", 1)
    if len(parts) < 2:
        unmatched[e["name"]] += 1; continue
    fn, ln = norm(parts[0]), norm(parts[1])
    cand = []
    if e["club"]:
        cand = by_club_full.get((e["club"], fn + ln), [])
        if not cand:
            cl = [p for p in by_club_last.get((e["club"], ln), []) if norm(p["first"])[:1] == fn[:1]]
            if len(cl) == 1:
                cand = cl
    if not cand:
        g = by_full.get(fn + ln, [])
        if len(g) == 1:
            cand = g
    if len(cand) != 1:
        unmatched[(e["club"], e["name"])] += 1; continue
    p = cand[0]
    slot = e["slot"]
    if slot == "R":
        slot = "R" if e["idx"] == 0 else "RR"
    p.setdefault("slots", Counter())[slot] += 1

MAP = {"F": "FWD", "HF": "FWD", "C": "MID", "HB": "DEF", "B": "DEF", "R": "RUC", "RR": "MID"}

def pos_of(p):
    s = p.get("slots")
    if not s:
        return "", ""
    c = Counter()
    for k, v in s.items():
        if k in MAP:
            c[MAP[k]] += v
    detail_s = " ".join(f"{k}:{v}" for k, v in sorted(s.items(), key=lambda kv: -kv[1]))
    if not c:
        return "", detail_s
    return c.most_common(1)[0][0], detail_s

# ---- write players
HDR = ["club", "sanfl_id", "first", "last", "num", "dob", "height_cm", "weight_kg", "real_pos", "sheet_slots",
       "gm", "gl", "bh", "di", "ki", "hb", "mk", "cm", "tk", "ho", "cl", "if50", "rb", "ff", "fa",
       "res_gm", "res_gl", "career_league_gm", "career_league_gl", "afl_listed", "afl_club", "afl_num", "afl_src",
       "src_roster", "src_stats"]
rows_main, rows_link = [], []
for p in players:
    d = p["d"]
    lg = season_stats(d, "sanfl")
    rs = season_stats(d, "reserves")
    link = afl_link(p["first"], p["last"], p["dob"], p["tc"])
    if not link and p["guide_afl"]:
        link = {"club": BY_CODE[p["tc"]][8], "num": "", "_src": "club guide AFL column"}
    pos, slots = pos_of(p)
    src_roster = []
    if p["in_api"]:
        src_roster.append(f"{API}/players/{p['tc']}/2026/sanfl")
    if p["in_guide"]:
        src_roster.append("https://images.sanfl.com.au/content/uploads/" + p["pdf"])
    row = {"club": p["cid"], "sanfl_id": p["pid"], "first": p["first"], "last": p["last"], "num": p["num"],
           "dob": p["dob"], "height_cm": p["height_cm"] if str(p["height_cm"]).isdigit() else "",
           "weight_kg": p["weight_kg"] if str(p["weight_kg"]).isdigit() else "",
           "real_pos": pos, "sheet_slots": slots,
           "res_gm": rs.get("gm", ""), "res_gl": rs.get("gl", ""),
           "career_league_gm": p["career_gm"], "career_league_gl": p["career_gl"],
           "afl_listed": "y" if link else "", "afl_club": link["club"] if link else "",
           "afl_num": link["num"] if link else "", "afl_src": link["_src"] if link else "",
           "src_roster": " ; ".join(src_roster),
           "src_stats": f"{API}/player/{p['pid']}" if d else ""}
    for k, _ in STAT:
        row[k] = lg.get(k, "") if d else ""
    if d and not lg:
        row["gm"] = 0
    (rows_link if (link and BY_CODE[p["tc"]][7] == "reserves") else rows_main).append(row)

for name, rows in (("sanfl_players_2026.csv", rows_main), ("sanfl_afl_listed_2026.csv", rows_link)):
    with open(f"{ROOT}/{name}", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HDR)
        w.writeheader()
        for r in sorted(rows, key=lambda r: (r["club"], int(r["num"]) if str(r["num"]).isdigit() else 999, r["last"])):
            w.writerow(r)

# ---- report
print("main", len(rows_main), "afl-linked", len(rows_link))
print(Counter(r["club"] for r in rows_main))
print(Counter(r["club"] for r in rows_link))
for k in HDR:
    filled = sum(1 for r in rows_main if str(r[k]) != "")
    print(f"{k:18s} {100*filled/len(rows_main):5.1f}%")
print("guide-AFL flag vs link:", sum(1 for p in players if p["guide_afl"]), "unmatched sheet names:", len(unmatched))
print("top unmatched:", unmatched.most_common(40))
