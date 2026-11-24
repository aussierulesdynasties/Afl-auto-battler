"""Where Google Earth's camera really was for an oblique shot, solved from the painted field lines.

  python3 tools/grounds/ge/ge_solve.py <ground> <views.json> <workdir> <boundary.json> <view> [<view> ...]

Google Earth does not always put the camera where the URL asks (it lifts low cameras; Cazaly's found its close
obliques off in position and angle too), and a side-on comparison is only as good as the camera behind it. The
painted lines are flat, known and on every ground, so they pin the camera down: the boundary line, the centre
square, the centre circles, both 50 m arcs and both goal squares are projected through a pinhole camera
(Google Earth's 25.58 deg vertical field of view over the 720-row crop that ge_shoot.js saves) and the camera
(position, heading, pitch, roll) is moved until they sit on the white lines found in the shot.

boundary.json is the per-ground file the match uses (/mnt/project-files/boundaries/<slug>.json): model metres
(glb x, glb z), {"line": [[x, z], ...], "goals": [[x, z], [x, z]], "centre": [x, z]}.

A solve is only trusted when the shot shows enough of the field (both 50 m arcs and the centre square must each
have at least MIN_INLIERS points on a line) and it ends inside the bounds rather than pressed against them (BOUND_M, BOUND_DEG); otherwise the fit can slide (Cazaly's: close obliques at the club end, with one
arc and no centre square, solved to a wrong pose). Untrusted solves are reported and not written.
Ported from the Cazaly's rebuild (tools/grounds/cazalys/work/measure/solve.py, PR #2034) to any ground."""
import json, math, os, sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd
from scipy.optimize import least_squares

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ge_compare as G  # noqa: E402

W, H = 1280, 720
F = (H / 2) / math.tan(math.radians(G.FOV / 2))
MIN_INLIERS = 40
BOUND_M, BOUND_DEG = 15.0, 2.0
WHITE = float(os.environ.get("GE_SOLVE_WHITE", "9"))


def field_lines(b):
    """Painted lines as named point sets in (east, north, 0) model metres."""
    en = lambda p: np.array([p[0], -p[1]], float)
    line = np.array([en(p) for p in b["line"]])
    g1, g2 = en(b["goals"][0]), en(b["goals"][1])
    c = en(b["centre"]) if "centre" in b else (g1 + g2) / 2
    ax = (g2 - g1) / np.linalg.norm(g2 - g1); px = np.array([-ax[1], ax[0]])
    # the boundary, densified
    seg = []
    for i in range(len(line)):
        a, z = line[i], line[(i + 1) % len(line)]
        n = max(2, int(np.linalg.norm(z - a) / 0.5))
        seg.append(a + np.outer(np.linspace(0, 1, n, endpoint=False), z - a))
    bnd = np.concatenate(seg)
    from matplotlib.path import Path
    inside = Path(line).contains_points
    out = {"boundary": bnd}
    t = np.linspace(0, 2 * np.pi, 1440, endpoint=False)
    for k, gp in (("arc_1", g1), ("arc_2", g2)):
        q = gp + 50 * np.stack([np.cos(t), np.sin(t)], 1)
        out[k] = q[inside(q)]
    s = np.linspace(-25, 25, 200)
    out["centre_square"] = np.concatenate([c + np.outer(s, ax) + k * px for k in (-25, 25)] +
                                          [c + k * ax + np.outer(s, px) for k in (-25, 25)])
    tt = np.linspace(0, 2 * np.pi, 200, endpoint=False)
    out["centre_circles"] = np.concatenate([c + r * np.stack([np.cos(tt), np.sin(tt)], 1) for r in (5.0, 1.5)])
    gs = []
    for gp, sg in ((g1, 1), (g2, -1)):   # goal squares: 6.4 m wide, 9 m deep into the field
        w, d = np.linspace(-3.2, 3.2, 40), np.linspace(0, 9, 50)
        gs += [gp + np.outer(w, px) + sg * 9 * ax, gp + 3.2 * px + sg * np.outer(d, ax), gp - 3.2 * px + sg * np.outer(d, ax)]
    out["goal_squares"] = np.concatenate(gs)
    return {k: np.c_[v, np.zeros(len(v))] for k, v in out.items()}


def axes(yaw, pitch, roll):
    f = np.array([math.sin(yaw) * math.cos(pitch), math.cos(yaw) * math.cos(pitch), math.sin(pitch)])
    r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r); u = np.cross(r, f)
    cr, sr = math.cos(roll), math.sin(roll)
    return f, cr * r + sr * u, -sr * r + cr * u


def project(p, P):
    f, r, u = axes(*p[3:6]); Q = P - p[:3]; z = Q @ f
    return np.stack([W / 2 + F * (Q @ r) / z, H / 2 - F * (Q @ u) / z], 1), z


def asked_pose(g, v, work):
    """The camera the URL asked for, lifted to Google Earth's readout like ge_compare.plan does."""
    e, n, u = v.get("at", [0, 0, 0])
    h, t, d = math.radians(v["h"]), math.radians(v["t"]), v["d"]
    dirv = np.array([math.sin(t) * math.sin(h), math.sin(t) * math.cos(h), -math.cos(t)])
    cam = np.array([e, n, u]) - d * dirv
    ro = G.readouts(os.path.join(work, "ge", v["name"] + "_cam.png"))
    if ro and ro[0][0] is not None:
        cam[2] = ro[0][0] - g["ge_alt"]
    return np.r_[cam, math.atan2(dirv[0], dirv[1]), math.asin(dirv[2]), 0.0]


def white_lines(im):
    a = np.asarray(im, float); bl = a[..., 2]
    top_hat = bl - nd.grey_opening(bl, size=(7, 7))
    green = (a[..., 1] > a[..., 0] + 2) & (a[..., 1] > a[..., 2] + 5)
    on_grass = nd.binary_dilation(green, iterations=6) & (nd.uniform_filter(green.astype(float), 25) > 0.6)
    m = (top_hat > WHITE) & on_grass
    m[:20] = False
    return m


def solve(gname, v, work, lines):
    g = G.GROUNDS[gname]
    im = Image.open(os.path.join(work, "ge", v["name"] + ".png")).convert("RGB")
    if im.size != (W, H):
        raise SystemExit("%s: expected a %dx%d ge_shoot crop" % (v["name"], W, H))
    m = white_lines(im)
    dt = nd.distance_transform_edt(~m)
    allp = np.concatenate(list(lines.values()))
    p0 = asked_pose(g, v, work)

    def res(p, cap):
        uv, z = project(p, allp)
        ok = (z > 0) & (uv[:, 0] > 2) & (uv[:, 0] < W - 3) & (uv[:, 1] > 2) & (uv[:, 1] < H - 3)
        dd = nd.map_coordinates(dt, [np.clip(uv[:, 1], 0, H - 1), np.clip(uv[:, 0], 0, W - 1)], order=1)
        return np.where(ok, np.minimum(dd, cap), cap)

    # Google Earth's camera never rolls (the URL's 0r), so roll stays 0: a free roll let a wrong pose fit the
    # lines (a test at Cazaly's slid 290 m with 19 deg of roll and still matched 1.4 px).
    q = p0[:5].copy()
    # Google Earth keeps the asked ground spot and heading and only lifts the camera (and its pitch follows), so the
    # spot and heading may only move within BOUND_M / BOUND_DEG of the asked ones; height and pitch are free.
    # Without this the fit slides along the view (a test at Cazaly's moved 140 m and still matched 1.4 px).
    big = 1e6
    lo = p0[:5] - [BOUND_M, BOUND_M, big, math.radians(BOUND_DEG), math.radians(30)]
    hi = p0[:5] + [BOUND_M, BOUND_M, big, math.radians(BOUND_DEG), math.radians(30)]
    for cap in (60, 25, 10, 5):
        q = least_squares(lambda x: res(np.r_[x, 0.0], cap), q, bounds=(lo, hi), loss="soft_l1", f_scale=cap / 3,
                          x_scale=[1, 1, 1, .01, .01], diff_step=[2e-3] * 3 + [2e-4] * 2).x
    p = np.r_[q, 0.0]
    cover, inl_d = {}, []
    for k, P in lines.items():
        uv, z = project(p, P)
        ok = (z > 0) & (uv[:, 0] > 2) & (uv[:, 0] < W - 3) & (uv[:, 1] > 2) & (uv[:, 1] < H - 3)
        d = dt[uv[ok, 1].round().astype(int), uv[ok, 0].round().astype(int)]
        cover[k] = int((d < 3).sum()); inl_d.append(d[d < 3])
    inl_d = np.concatenate(inl_d)
    moved = float(np.linalg.norm(p[:2] - p0[:2])); turned = abs(math.degrees(p[3] - p0[3]))
    trusted = (all(cover.get(k, 0) >= MIN_INLIERS for k in ("arc_1", "arc_2", "centre_square"))
               and moved < BOUND_M - 0.5 and turned < BOUND_DEG - 0.05)
    rms = float(np.sqrt((inl_d ** 2).mean())) if len(inl_d) else float("nan")
    out = dict(view=v["name"], trusted=trusted, rms_px=round(rms, 2), inliers=cover,
               camera_east_north_up=[round(float(x), 2) for x in p[:3]],
               heading_deg=round(math.degrees(p[3]), 2), pitch_deg=round(math.degrees(p[4]), 2), roll_deg=round(math.degrees(p[5]), 2),
               moved_from_asked_m=[round(float(x), 2) for x in p[:3] - p0[:3]],
               turned_from_asked_deg=[round(math.degrees(x), 2) for x in p[3:] - p0[3:]])
    o = im.copy(); a = np.asarray(o).copy(); a[m] = [255, 0, 255]; o = Image.fromarray(a); dr = ImageDraw.Draw(o)
    uv, z = project(p, allp)
    for q, zz in zip(uv, z):
        if zz > 0:
            dr.point(tuple(q), fill=(0, 255, 255))
    o.save(os.path.join(work, v["name"] + "_solve.png"))
    return out


if __name__ == "__main__":
    gname, vf, work, bf = sys.argv[1:5]
    V = {v["name"]: v for v in json.load(open(vf))}
    lines = field_lines(json.load(open(bf)))
    done = {}
    for name in sys.argv[5:]:
        r = solve(gname, V[name], work, lines)
        print(json.dumps(r))
        if r["trusted"]:
            done[name] = r
        else:
            print("  %s: not trusted (needs both 50 m arcs and the centre square in view): not written" % name)
    path = os.path.join(work, "solved.json")
    old = json.load(open(path)) if os.path.exists(path) else {}
    old.update(done)
    json.dump(old, open(path, "w"), indent=1)
