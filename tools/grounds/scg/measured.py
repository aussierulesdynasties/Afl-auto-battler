"""Gathers the round-5 measurements into tools/grounds/scg/measured.json, which facades.py builds from.

    python3 tools/grounds/scg/measured.py <workdir>

From <workdir>/hover.json (hover.py: Google Earth's own heights and positions under the mouse) each nearby
building's outline (its long walls moved to where the roof really ends), eave and ridge over the ground
beside it (rounded to 0.1 m), and the ground's height over the SCG's turf; and from <workdir>/colour_cal.json
(colour_cal.py: graphics-card renders against Google Earth) its roof colour, the roof's current colour times
the measured factor (linear light, capped at 1). A height or wall Google Earth's readouts didn't settle
(fewer than 4 readouts over 2.5 m above the land, a wall with no clear drop from roof to ground) keeps facades.py's value.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)


def main(work):
    import facades as fc
    hv = json.load(open(os.path.join(work, "hover.json")))
    cc = json.load(open(os.path.join(work, "colour_cal.json"))) if os.path.exists(os.path.join(work, "colour_cal.json")) else {"roofs": {}}
    unm = {"u%d" % e["ge_blob"]: e for e in json.load(open(os.path.join(ROOT, "unmapped.json")))}
    out = {}
    for name, r in hv.items():
        if name.startswith("u") and (name not in unm or "measured" in unm[name]):
            continue        # dropped, or re-measured on the hover grid since (unmapped.json carries its numbers)
        hits = r.get("roof_hits", 0)
        m = {"ground_over_turf": round(r["ground_over_turf"], 1),
             "source": "Google Earth status-bar readouts, %d of %d on the roof" % (hits, r["roof_points"])}
        if hits >= 4 and "eave" in r:
            m["eave"] = round(r["eave"], 1)
            if r.get("ridge") is not None:
                m["ridge"] = round(max(r["ridge"], r["eave"]), 1)
            m["roof_spread_m"] = round(r["roof_spread"], 1)
        if any(v is not None for v in r.get("wall_moves", {}).values()):
            m["outline"] = r["outline"]
            m["wall_moves_m"] = r["wall_moves"]
        out[name] = m
    for name, c in cc.get("roofs", {}).items():
        key = int(name) if name.isdigit() else None
        if key is not None and key in fc.SPEC:
            old = fc.SPEC[key][4]
        elif name in unm and "measured" not in unm[name]:
            old = getattr(fc, unm[name]["roof_colour"])
        else:
            continue
        out.setdefault(name, {})["roof_colour"] = [round(min(1.0, o * f), 3) for o, f in zip(old, c["factor"])]
        out[name]["roof_colour_ge_srgb"] = [int(x) for x in c["ge"]]
    json.dump(out, open(os.path.join(ROOT, "measured.json"), "w"), indent=1, sort_keys=True)
    print("%d buildings measured" % len(out))


if __name__ == "__main__":
    main(sys.argv[1])
