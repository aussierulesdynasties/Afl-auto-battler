"""The SCG's four big roofs rebuilt to Google Earth's measured edges and heights (SCG rebuild round 5, 2026-11-23).

Hovering Google Earth every 2.5 degrees round the ground (qa/roof_ge.json: each bearing's first and last roof
readout from straight-down views, and the roof's height) showed the model's roofs (#1909, guessed in its
source) were off by metres:

    stand (bearings)                 Google Earth: front - back @ height      the model before
    Messenger, Noble, Bradman (N)    95-99 - 125-137 m @ 34 m                 101-108 - 132-134 m @ 28-36 m, sloped
    east stands                      85 - 106-110 m @ 21 m                    84-88 - 107-111 m @ 25 m
    Trumper side (S)                 91-94 - 120-123 m @ 26 m                 98-102 - 125-130 m @ 30-36 m
    west stands                      88-93 - 110-122 m @ 22 m                 84-90 - 110-117 m @ 18 m

Bending the model's own roof to those numbers rippled it and tore the stand ends, so this replaces them.
It always starts from the model as it was at SOURCE (git), so re-running it gives the same result:

1. Out of the shipped glbs (scg_part1/2.glb), in each stand's bearings: the old roof (materials DEL).
2. The new roofs, a PART (assets/grounds/scg/roofs.bin, GroundModels.PARTS): per half degree a flat slab at
   Google Earth's height between a front and a back edge, each edge the measured readouts (a median of three
   bearings, half the 1.5 m readout step outward: the first and last readout lie inside the edge) smoothed
   with a running mean over 5 degrees; a fascia on the front and back, an underside, caps at the ends. The
   Messenger roof's inner band is glazed, as Google Earth shows it.
3. Under them: anything the old roof was carrying above the new underside (back walls, cladding, glazing)
   is cut to it; where the new roof stands higher than the old walls (the west), a clad band closes the gap.
4. The south stand's back: Google Earth has open ground from 124 m on bearings 140-185, but the model's
   seats ran to 129 m. Everything past the roof's back edge less CUT m moves in to it; the seating deck
   (RAKE) slides down its own slope as it comes in (the rise per metre fitted to the back rows' seats), so
   the rows in front keep their pitch and nothing hangs over them. Seats within a row of that line come out.
   An old-roof primitive left with no triangles is dropped with its accessor (Godot refuses a glb with one).
5. The big screen (bearings 55-65): its top reads 21 m in Google Earth; the model's stood at 25.6 m, over
   the new east roof. It moves down whole.

The heritage stands (north-west) sit within 2 m of Google Earth already and are left alone. Run boxes.py
after this (its glass band reaches up to these roofs), then import and the shared seat rule (it took 13 more
seats out over the south-east corner's cut, where the deck's triangles no longer reach under them):

    python3 tools/grounds/scg/stand_roofs.py
    python3 tools/grounds/scg/boxes.py
    godot --headless --path . --import
    godot --headless --path . --script tools/grounds/seat_check.gd -- --write scg

Model axes: x east, y up, z south; PC is the pitch centre.
"""
import json
import os
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from messenger_roof import read, write, view, get3_fast, put3, indices   # noqa: E402

DIR = os.path.join(ROOT, "..", "..", "..", "assets", "grounds", "scg")
PC = np.array([0.94, 11.82])
RAKE = ("conc",)              # the seating decks
SOURCE = "d804a81d"           # the model and seats this starts from (round 5's buildings, before the roofs)
# stand: first and last bearing of the new roof (the survey's end bearings, half a step out)
SECTORS = {"N": (343.75, 43.75), "E": (66.25, 118.75), "S": (118.75, 191.25), "W": (191.25, 283.75)}
DEL = ("roof", "roofu", "fascia", "glassroof", "rail", "steel")
SCREEN = ("sbface", "sbad", "sbback")
SCREEN_TOP = 21.0
STEP = 0.75                   # half the survey's 1.5 m readout spacing
SMOOTH = 5.0                  # degrees of running mean on the edges
CUT = 1.5
THICK_FRONT, THICK_BACK = 1.1, 1.8
GLAZED = {"N": 6.5}           # m of glazing along the front edge
TOP = (0.70, 0.70, 0.66)      # linear: Google Earth's roofs read about (220, 220, 212)
# Roof undersides: grey with a faint green tint (director, 2026-11-21), about (85, 90, 82) on screen. They
# face down, where the match light is a dim blue-violet: on the PC's GPU a (0.24, 0.27, 0.25) underside
# rendered (49, 48, 78), slate violet. So they are painted warm and green, as Marvel's are
# (docs/MCG_STANDARD.md), by that render's light per channel.
UNDER = (0.71, 0.93, 0.28)
RAFTER = (0.52, 0.68, 0.22)   # the steel under them, a shade darker so it reads against the sheet
RAFTER_EVERY = 7.5            # m along the front edge between rafters
RAFTER_W, RAFTER_D = 0.35, 0.9   # width, depth under the sheet (m)
PURLIN_D = 0.35               # the two runs along the roof, at a third and two thirds of its depth
FASCIA = (0.55, 0.55, 0.52)
GLASS = (0.10, 0.14, 0.17)
CLAD = (0.42, 0.44, 0.44)


def bearing(x, z):
    return (np.degrees(np.arctan2(x - PC[0], -(z - PC[1]))) + 360.0) % 360.0


def unwrap(b, a0):
    return a0 + (b - a0) % 360.0


def edges():
    """Per sector: bearings (unwrapped from its start, every 0.5 deg) and the front, back and height there."""
    g = json.load(open(os.path.join(ROOT, "qa", "roof_ge.json")))["roofs"]
    out = {}
    for name, (a0, a1) in SECTORS.items():
        span = (a1 - a0) % 360.0
        rows = sorted((unwrap(float(k), a0), v) for k, v in g.items() if unwrap(float(k), a0) - a0 <= span)
        bs = np.array([b for b, _ in rows])
        v = np.array([r for _, r in rows])
        med = lambda c: np.array([np.median(c[max(0, i - 1):i + 2]) for i in range(len(c))])
        f, k = med(v[:, 0]) - STEP, med(v[:, 1]) + STEP
        bb = np.arange(a0, a0 + span + 1e-6, 0.5)
        fi, ki = np.interp(bb, bs, f), np.interp(bb, bs, k)
        n = int(SMOOTH / 0.5) // 2
        sm = lambda c: np.array([c[max(0, i - n):i + n + 1].mean() for i in range(len(c))])
        fs, ks = sm(fi), sm(ki)
        h = float(np.median(v[:, 2]))
        res = np.r_[np.abs(np.interp(bs, bb, fs) - (v[:, 0] - STEP)), np.abs(np.interp(bs, bb, ks) - (v[:, 1] + STEP))]
        print("%s: %.0f m over the turf; front %.1f-%.1f m, back %.1f-%.1f m; the smoothed edges are within %.1f m "
              "of %d%% of the readouts, %.1f m of all" % (name, h, fs.min(), fs.max(), ks.min(), ks.max(),
                                                         np.percentile(res, 80), 80, res.max()))
        out[name] = (bb, fs, ks, h)
    return out


def sector_of(b, E):
    """Per bearing: the sector's name ('' outside) and its front, back and height there."""
    name = np.full(b.shape, "", object)
    f, k, h = np.full(b.shape, np.nan), np.full(b.shape, np.nan), np.full(b.shape, np.nan)
    for s, (a0, a1) in SECTORS.items():
        u = unwrap(b, a0)
        m = (u - a0) <= (a1 - a0) % 360.0
        bb, fs, ks, hh = E[s]
        name[m] = s
        f[m], k[m], h[m] = np.interp(u[m], bb, fs), np.interp(u[m], bb, ks), hh
    return name, f, k, h


tris = []


def quad(p0, p1, p2, p3, col):
    n = np.cross(np.subtract(p1, p0), np.subtract(p3, p0))
    ln = np.linalg.norm(n)
    if ln < 1e-9:
        return
    n = n / ln
    for t in ((p0, p1, p2), (p0, p2, p3)):
        for p in t:
            tris.extend([float(x) for x in p] + [float(x) for x in n] + list(col))


def at(b, r, y):
    t = np.radians(b)
    return (PC[0] + r * np.sin(t), y, PC[1] - r * np.cos(t))


def build_roof(name, bb, fs, ks, h, wall_top):
    """The slab, fascias, underside and caps; the glazed band; the clad band up from wall_top."""
    def th(t):
        return THICK_FRONT + (THICK_BACK - THICK_FRONT) * t
    gl = GLAZED.get(name, 0.0)
    for i in range(len(bb) - 1):
        b0, b1 = bb[i], bb[i + 1]
        f0, f1, k0, k1 = fs[i], fs[i + 1], ks[i], ks[i + 1]
        # top: glazed band, then the sheet (normal up: a quad wound so its cross product points up)
        g0, g1 = min(f0 + gl, k0 - 1), min(f1 + gl, k1 - 1)
        if gl:
            quad(at(b0, f0, h), at(b0, g0, h), at(b1, g1, h), at(b1, f1, h), GLASS)
        quad(at(b0, g0 if gl else f0, h), at(b0, k0, h), at(b1, k1, h), at(b1, g1 if gl else f1, h), TOP)
        # underside, sloping down to the back as the slab thickens
        quad(at(b0, f0, h - th(0)), at(b1, f1, h - th(0)), at(b1, k1, h - th(1)), at(b0, k0, h - th(1)), UNDER)
        # front fascia (facing the field) and back fascia
        quad(at(b0, f0, h - th(0)), at(b0, f0, h), at(b1, f1, h), at(b1, f1, h - th(0)), FASCIA)
        quad(at(b0, k0, h - th(1)), at(b1, k1, h - th(1)), at(b1, k1, h), at(b0, k0, h), FASCIA)
        # the clad band from the old back wall's top to the underside, just inside the back edge
        w0, w1 = wall_top[i], wall_top[i + 1]
        top_y = h - th(1)
        if not (np.isnan(w0) or np.isnan(w1)) and min(w0, w1) < top_y - 0.3:
            r0, r1 = k0 - 0.8, k1 - 0.8
            quad(at(b0, r0, min(w0, top_y) - 0.2), at(b1, r1, min(w1, top_y) - 0.2), at(b1, r1, top_y), at(b0, r0, top_y), CLAD)
            quad(at(b1, r1, min(w1, top_y) - 0.2), at(b0, r0, min(w0, top_y) - 0.2), at(b0, r0, top_y), at(b1, r1, top_y), CLAD)
    # the steel under the sheet: radial rafters every RAFTER_EVERY m of the front edge, two purlins along it
    def under_y(r, f, k):
        return h - th(min(max((r - f) / max(k - f, 1e-6), 0.0), 1.0))

    def beam(b0, b1, r0, r1, f0, f1, k0, k1, depth):
        # a box hung under the sheet from (b0, r0) to (b1, r1): two sides and a bottom
        ya, yb = under_y(r0, f0, k0), under_y(r1, f1, k1)
        rad = np.radians
        da = np.array([np.sin(rad(b1)) * r1 - np.sin(rad(b0)) * r0, -np.cos(rad(b1)) * r1 + np.cos(rad(b0)) * r0])
        side = np.array([-da[1], da[0]]) / max(np.linalg.norm(da), 1e-6) * (RAFTER_W / 2)
        p0, p1 = np.array(at(b0, r0, 0.0)), np.array(at(b1, r1, 0.0))
        def pt(p, sgn, y):
            return (p[0] + sgn * side[0], y, p[2] + sgn * side[1])
        for sgn in (-1, 1):
            quad(pt(p0, sgn, ya), pt(p1, sgn, yb), pt(p1, sgn, yb - depth), pt(p0, sgn, ya - depth), RAFTER)
        quad(pt(p0, -1, ya - depth), pt(p1, -1, yb - depth), pt(p1, 1, yb - depth), pt(p0, 1, ya - depth), RAFTER)

    arc = np.concatenate([[0.0], np.cumsum(np.radians(np.diff(bb)) * (fs[:-1] + fs[1:]) / 2)])
    n_r = max(int(arc[-1] // RAFTER_EVERY), 1)
    for s_ in np.linspace(arc[-1] / (2 * n_r), arc[-1] - arc[-1] / (2 * n_r), n_r):
        b = float(np.interp(s_, arc, bb))
        f, k = float(np.interp(b, bb, fs)), float(np.interp(b, bb, ks))
        beam(b, b, f + 0.3, k - 0.3, f, f, k, k, RAFTER_D)
    for t in (1 / 3, 2 / 3):
        for i in range(len(bb) - 1):
            r0 = fs[i] + (ks[i] - fs[i]) * t
            r1 = fs[i + 1] + (ks[i + 1] - fs[i + 1]) * t
            beam(bb[i], bb[i + 1], r0, r1, fs[i], fs[i + 1], ks[i], ks[i + 1], PURLIN_D)
    # end caps
    for i, s in ((0, 1), (len(bb) - 1, -1)):
        b, f, k = bb[i], fs[i], ks[i]
        p = [at(b, f, h - th(0)), at(b, k, h - th(1)), at(b, k, h), at(b, f, h)]
        quad(*(p if s > 0 else p[::-1]), FASCIA)


def main():
    E = edges()
    paths = [os.path.join(DIR, "scg_part1.glb"), os.path.join(DIR, "scg_part2.glb")]
    seat_files = sorted(f for f in os.listdir(DIR) if f.startswith("seats_") and f.endswith(".bin"))
    for f in ["scg_part1.glb", "scg_part2.glb"] + seat_files:
        data = subprocess.run(["git", "show", "%s:assets/grounds/scg/%s" % (SOURCE, f)], cwd=ROOT,
                              capture_output=True, check=True).stdout
        open(os.path.join(DIR, f), "wb").write(data)
    parts = [(p,) + read(p) for p in paths]

    # the south rake's rise per metre at each bearing, from its upper seats (a line through each 5 degrees;
    # the last one holds to the sector's end)
    st = np.concatenate([np.fromfile(os.path.join(DIR, f), "<f4").reshape(-1, 12)[:, [3, 7, 11]] for f in seat_files])
    sb, sr = bearing(st[:, 0], st[:, 2]), np.hypot(st[:, 0] - PC[0], st[:, 2] - PC[1])
    rise_b, rise = [], []
    # (only the back 14 m, the upper deck the cut runs through; past 190 the bins mix in the next stand)
    for b0 in np.arange(117.5, 190.0, 2.5):
        kb = float(np.interp(b0 + 1.25, E["S"][0], E["S"][2])) - CUT
        m = (sb >= b0) & (sb < b0 + 2.5) & (sr > kb - 14.0)
        if m.sum() > 30:
            rise_b.append(b0 + 1.25)
            rise.append(float(np.polyfit(sr[m], st[m, 1], 1)[0]))
    print("south rake rise per metre: %.2f-%.2f" % (min(rise), max(rise)))

    # the old back walls' top under each new roof's back edge (for the clad band), before anything is cut
    pts = []
    for _p, j, bin_ in parts:
        for pr in j["meshes"][0]["primitives"]:
            nm = j["materials"][pr["material"]]["name"]
            if nm in DEL or nm in SCREEN or nm in ("tower", "lamp", "headback", "fence"):
                continue
            v = get3_fast(bin_, view(j, bin_, pr["attributes"]["POSITION"]))
            pts.append(np.c_[bearing(v[:, 0], v[:, 2]), np.hypot(v[:, 0] - PC[0], v[:, 2] - PC[1]), v[:, 1]])
    pts = np.concatenate(pts)
    walls = {}
    for s, (bb, fs, ks, h) in E.items():
        wt = np.full(len(bb), np.nan)
        for i, b in enumerate(bb):
            m = (np.abs((pts[:, 0] - b + 180.0) % 360.0 - 180.0) < 1.0) & (np.abs(pts[:, 1] - ks[i]) < 4.0)
            if m.any():
                wt[i] = pts[m, 2].max()
        walls[s] = wt

    screen_top = max(float(get3_fast(b_, view(j_, b_, pr["attributes"]["POSITION"]))[:, 1].max())
                     for _p, j_, b_ in parts for pr in j_["meshes"][0]["primitives"]
                     if j_["materials"][pr["material"]]["name"] in SCREEN)
    removed = cut = 0
    for path, j, bin_ in parts:
        for pr in j["meshes"][0]["primitives"]:
            nm = j["materials"][pr["material"]]["name"]
            acc = pr["attributes"]["POSITION"]
            idx = view(j, bin_, acc)
            v = get3_fast(bin_, idx)
            b = bearing(v[:, 0], v[:, 2])
            r = np.hypot(v[:, 0] - PC[0], v[:, 2] - PC[1])
            sec, f, k, h = sector_of(b, E)
            if nm in DEL:
                # 1. the old roof out: its triangles in a stand's bearings dropped from the index buffer
                ia = j["accessors"][pr["indices"]]
                tri = indices(j, bin_, pr["indices"]).reshape(-1, 3)
                cb = bearing(v[tri, 0].mean(1), v[tri, 2].mean(1))
                keep = sector_of(cb, E)[0] == ""
                removed += int((~keep).sum())
                kept = tri[keep].ravel()
                bv = j["bufferViews"][ia["bufferView"]]
                off = bv.get("byteOffset", 0) + ia.get("byteOffset", 0)
                dt = {5123: "<u2", 5125: "<u4", 5121: "u1"}[ia["componentType"]]
                raw = np.frombuffer(bin_, np.uint8)
                new = kept.astype(dt).view(np.uint8)
                raw[off:off + len(new)] = new
                ia["count"] = int(len(kept))
                continue
            if nm in SCREEN:
                v2 = v - [0.0, screen_top - SCREEN_TOP, 0.0]
            elif nm in ("tower", "lamp", "headback", "fence"):
                continue
            else:
                v2 = v.copy()
                ins = (sec != "")
                under = h - THICK_BACK
                # 4. (done first) the south stand's back in to the roof's back edge
                sm = (sec == "S") & (r > k - CUT)
                rr = np.where(sm, np.minimum(r, k - CUT), r)
                s_ = np.where(r > 1e-6, rr / np.maximum(r, 1e-6), 1.0)
                v2[:, 0] = PC[0] + (v2[:, 0] - PC[0]) * s_
                v2[:, 2] = PC[1] + (v2[:, 2] - PC[1]) * s_
                if nm in RAKE:
                    # the rake itself is cut, not squeezed: a point past the new back slides down its own slope
                    # to it, so the rows in front keep their pitch and nothing hangs over the seats
                    v2[sm, 1] -= np.interp(b[sm], rise_b, rise) * (r[sm] - rr[sm])
                # 3. walls and glazing the old roof carried, cut to the new underside (by where they now stand)
                m = ins & (rr > f - 1.0) & (rr < k + 3.0) & (v[:, 1] > under)
                v2[m, 1] = under[m]
            ch = np.abs(v2 - v).max(1) > 0.005
            if not ch.any():
                continue
            cut += int(ch.sum())
            put3(bin_, idx, v2.astype(np.float32))
            a = j["accessors"][acc]
            a["min"] = [float(x) for x in v2.min(0)]
            a["max"] = [float(x) for x in v2.max(0)]
        # a primitive left with no triangles is invalid glTF (an accessor's count is at least 1), and Godot
        # then mixes up the surfaces after it (towers and the south glazing vanished): drop it
        for me in j["meshes"]:
            me["primitives"] = [pr for pr in me["primitives"] if j["accessors"][pr["indices"]]["count"] > 0]
        # and the empty index accessors themselves (Godot checks every accessor), renumbering the rest
        keep_acc = [i for i, a in enumerate(j["accessors"]) if a["count"] > 0]
        renum = {old_i: new_i for new_i, old_i in enumerate(keep_acc)}
        j["accessors"] = [j["accessors"][i] for i in keep_acc]
        for me in j["meshes"]:
            for pr in me["primitives"]:
                pr["indices"] = renum[pr["indices"]]
                pr["attributes"] = {k_: renum[a_] for k_, a_ in pr["attributes"].items()}
        write(path, j, bin_)
    print("old roof: %d triangles out; %d vertices cut to the new roofs or brought in" % (removed, cut))

    for s, (bb, fs, ks, h) in E.items():
        build_roof(s, bb, fs, ks, h, walls[s])
    np.array(tris, "<f4").tofile(os.path.join(DIR, "roofs.bin"))
    print("roofs.bin: %d triangles" % (len(tris) // 27))

    _f, _k, _h = None, None, None
    for f in seat_files:
        S = np.fromfile(os.path.join(DIR, f), "<f4").reshape(-1, 12)
        b = bearing(S[:, 3], S[:, 11])
        r = np.hypot(S[:, 3] - PC[0], S[:, 11] - PC[1])
        sec, _f, k, _h = sector_of(b, E)
        # a row clear of the new back: the last row sits on the deck, not on the slid edge (a real rear aisle)
        drop = (sec == "S") & (r > k - CUT - 1.2)
        S[~drop].astype("<f4").tofile(os.path.join(DIR, f))
        print("%s: %d seats behind the south stand's new back out, %d left" % (f, int(drop.sum()), int((~drop).sum())))


if __name__ == "__main__":
    main()
