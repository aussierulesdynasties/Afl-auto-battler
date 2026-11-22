"""Google Earth against our model from the same camera: the one shared tool for every ground (docs/MCG_STANDARD.md).

Pictures:
  python3 tools/grounds/ge/ge_compare.py plan  <ground> <views.json> <workdir>   # GE urls + our camera specs
  node    tools/grounds/ge/ge_shoot.js <workdir> --level                         # once per ground: GE's turf height,
  python3 tools/grounds/ge/ge_compare.py level <ground> <views.json> <workdir>   #   read back: set ge_alt in grounds.json
  node    tools/grounds/ge/ge_shoot.js <workdir>                                 # Google Earth shots (Playwright)
  python3 tools/grounds/ge/ge_compare.py plan  <ground> <views.json> <workdir>   # again: ours where GE's camera really was
  godot --path . --rendering-method mobile --script tools/visual/preinspect_look.gd -- <workdir>/ours <slug> $(cat <workdir>/specs.txt)
  python3 tools/grounds/ge/ge_compare.py sheet <ground> <views.json> <workdir> <out.jpg> [title]
Numbers (measured, never by eye):
  python3 tools/grounds/ge/ge_compare.py register <ground> <views.json> <workdir> <view>   # straight-down view: is the model where GE is?
  python3 tools/grounds/ge/ge_compare.py outline  <ground> <views.json> <workdir> <view>   # straight-down view: our edges vs GE's, metres
  python3 tools/grounds/ge/ge_solve.py ...                                                  # an oblique's true camera from the field lines

A view is {"name", "h" heading deg, "t" tilt deg (0 = straight down), "d" range m, "at" [east, north, up] m from
the model's origin}. Our camera is the same: target - d * (sin t sin h, sin t cos h, -cos t) in (east, north, up),
then through the match's fit (GroundModels.FIT) into match metres. Google Earth lifts a camera it thinks
too low (keeping its spot and tilt), so once the shots exist, plan reads where each one really was (the status bar
ge_shoot.js saves beside each shot, read with tesseract) and lifts ours the same; without tesseract it warns and
leaves ours where asked, and a low view's pair is then not to be trusted for sizes.

What goes wrong, so far (2026-11-22, from the shape audit of every ground):
- FOV: the URL's 35y is the vertical field of view of the whole 1000 px window; the 720-row crop is 25.58 deg.
  Per-ground copies used 23.5 deg and drew ours 8% too close.
- Turf height: always Google Earth's own (status bar, `--level`), never a map's: Adelaide is 26 m in GE, not 40.
- A fresh page per shot (a hash-only change shows the globe), and about 70 s of streaming on cloud swiftshader.
- Lining up: a search that starts 20-40 m off sticks on a wrong match. `register` searches 60 m and only uses
  the stadium's own edges (radius 160 m), so surroundings cannot pull it; it also reports the turn, which catches
  a model built in an oval-aligned frame instead of north-up (Traeger: 25 deg and 10 m out).
- Aerial photos lean: tall things sit 5-7 m off their footprints where GE has no 3D mesh (Barossa). Trace ground
  lines (wall feet, stand fronts, slab edges, where shadows start) there.
- Cloud renders (lavapipe, Mobile) never sunlight StandardMaterial3D: judge colour on a PC GPU; shape and size
  from the cloud are fine."""
import json, math, os, sys

UNDER_TURF = 0.1
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
# Per ground (grounds.json): the model origin's lat/lon (model x east, -z north) and Google Earth's turf height
# (m above sea level, read off GE's status bar with the mouse on the grass: `ge_shoot.js <workdir> --level`).
# The match fit comes from GroundModels.FIT (centre x, centre z, floor y, long axis deg, half length, half width),
# unless grounds.json gives one (a ground whose fit is not on main yet).


def _fits():
    import re
    gm = open(os.path.join(REPO, "scripts", "ui", "match", "GroundModels.gd")).read()
    body = gm.split("const FIT", 1)[1].split("\n}", 1)[0]
    return {k: [float(x) for x in v.split(",")] for k, v in re.findall(r'"(\w+)":\s*\[([^\]]+)\]', body)}


def load_grounds():
    fits = _fits()
    out = {}
    for k, g in json.load(open(os.path.join(HERE, "grounds.json"))).items():
        if k.startswith("_"):
            continue
        g = dict(g)
        g.setdefault("fit", fits.get(k))
        out[k] = g
    return out


GROUNDS = load_grounds()
# Google Earth's camera, measured 2026-11-22 at Adelaide and the MCG by hovering the mouse over points whose
# place on screen was worked out beforehand (the status bar gives the lat/lon under the mouse; every point fell
# within a metre at 60-150 m): the URL's "35y" is the vertical field of view of the whole browser window
# (1280 x 1000 in ge_shoot.js), centred on the window, and the "a" altitude is the look-at point's height
# above sea level. ge_shoot.js keeps rows 140-860 of it, so our matching picture (16:9 like the crop) needs the
# vertical field of view of those 720 rows.
GE_FOV, GE_WIN_H, GE_CROP_H = 35.0, 1000, 720
FOV = 2 * math.degrees(math.atan(math.tan(math.radians(GE_FOV / 2)) * GE_CROP_H / GE_WIN_H))   # 25.58


def to_match(g, p):
    """Model metres (x east, y up, z -north) -> match metres."""
    cx, cz, fy, ang, hl, hw = g["fit"]
    sx, sz = 1.0, 1.0   # every ground plays at its own size (#1949): nothing stretched
    a = math.radians(ang)
    x, y, z = p[0] - cx, p[1] - fy, p[2] - cz
    rx, rz = x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)
    return (rx * sx, y - UNDER_TURF, rz * sz)


def latlon(g, east, north):
    k = 111320.0
    return g["lat"] + north / 110574.0, g["lon"] + east / (k * math.cos(math.radians(g["lat"])))


def readouts(path):
    """[(camera m above sea level or None, height m under the centre or None)] from a status-bar strip."""
    import re, shutil, subprocess
    if not (os.path.exists(path) and shutil.which("tesseract")):
        return []
    from PIL import Image
    im = Image.open(path).convert("L")
    big = path[:-4] + "_x4.png"
    im.resize((im.width * 4, im.height * 4), Image.LANCZOS).save(big)
    txt = subprocess.run(["tesseract", big, "-", "--psm", "6"], capture_output=True, text=True).stdout
    os.remove(big)
    out = []
    num = lambda v, unit: float(v.replace(",", "")) * (1000.0 if unit.startswith("k") else 1.0)
    for line in txt.splitlines():
        c = re.search(r"Camera:\s*(-?[\d.,]+)\s*(km|m)", line)
        h = re.search(r"[EW]\s+(-?[\d.,]+)\s*(km|m)\s*$", line.strip())
        if c or h:
            out.append((num(*c.groups()) if c else None, num(*h.groups()) if h else None))
    return out


def level(gname, work):
    r = [h for _, h in readouts(os.path.join(work, "ge", "_level.png")) if h is not None]
    if not r:
        print("no readouts (run ge_shoot.js <workdir> --level first; needs tesseract)"); return
    r.sort()
    print("Google Earth turf heights round %s's centre: %s m; median %.0f m (GROUNDS ge_alt is %.0f)"
          % (gname, ", ".join("%.0f" % x for x in r), r[len(r) // 2], GROUNDS[gname]["ge_alt"]))


def plan(gname, views, work):
    g = GROUNDS[gname]
    os.makedirs(os.path.join(work, "ge"), exist_ok=True)
    urls, specs = [], []
    for v in views:
        if "cam" in v:
            # A fixed camera (a Street View or photosphere position, east/north/up m from the field centre)
            # looking along heading h, pitch p (deg, negative down); its reference picture is supplied
            # by hand as <work>/ge/<name>.png.
            ce, cn, cu = v["cam"]
            h, pp = math.radians(v["h"]), math.radians(v.get("p", 0.0))
            tgt = (ce + 100 * math.cos(pp) * math.sin(h), cn + 100 * math.cos(pp) * math.cos(h), cu + 100 * math.sin(pp))
            pc = to_match(g, (ce, cu, -cn))
            pt = to_match(g, (tgt[0], tgt[2], -tgt[1]))
            specs.append("%s:%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.1f" % ((v["name"],) + pc + pt + (v.get("fov", FOV),)))
            continue
        e, n, u = v.get("at", [0, 0, 0])
        h, t, d = math.radians(v["h"]), math.radians(v["t"]), v["d"]
        lat, lon = latlon(g, e, n)
        urls.append([os.path.join(work, "ge", v["name"] + ".png"),
                     "https://earth.google.com/web/@%.7f,%.7f,%.1fa,%.1fd,%gy,%.1fh,%.1ft,0r" % (lat, lon, g["ge_alt"] + u, d, GE_FOV, v["h"], v["t"])])
        dirv = (math.sin(t) * math.sin(h), math.sin(t) * math.cos(h), -math.cos(t))
        cam = (e - d * dirv[0], n - d * dirv[1], u - d * dirv[2])
        # Straight down: world up is the view direction, so tell preinspect_look which way north is (the old
        # 3-degree nudge south tilted every roof 5% of its height off its footprint).
        up = None
        if v["t"] < 3:
            o, nn = to_match(g, (0, 0, 0)), to_match(g, (0, 0, -1))
            up = (nn[0] - o[0], nn[1] - o[1], nn[2] - o[2])
        tgt = (e, n, u)
        ro = readouts(os.path.join(work, "ge", v["name"] + "_cam.png"))
        if ro and ro[0][0] is not None:
            # where Google Earth really put it: same spot and tilt, its own height (the readout is to the metre)
            lift = ro[0][0] - g["ge_alt"] - cam[2]
            if abs(lift) > 1.5:
                print("%s: Google Earth's camera is %+.0f m from the asked height; ours follows it" % (v["name"], lift))
                cam = (cam[0], cam[1], cam[2] + lift)
                tgt = (tgt[0], tgt[1], tgt[2] + lift)
        elif os.path.exists(os.path.join(work, "ge", v["name"] + ".png")):
            print("%s: no camera readout (tesseract missing?): ours sits where asked, which can be under Google Earth's" % v["name"])
        pc = to_match(g, (cam[0], cam[2], -cam[1]))
        pt = to_match(g, (tgt[0], tgt[2], -tgt[1]))
        spec = "%s:%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f" % ((v["name"],) + pc + pt + (v.get("fov", FOV),))
        if up:
            spec += ",%.4f,%.4f,%.4f" % up
        specs.append(spec)
    json.dump(urls, open(os.path.join(work, "urls.json"), "w"), indent=1)
    # Straight down on the field centre from 500 m, for reading Google Earth's turf height (ge_shoot.js --level).
    json.dump("https://earth.google.com/web/@%.7f,%.7f,%.1fa,500d,%gy,0h,0t,0r" % (g["lat"], g["lon"], g["ge_alt"], GE_FOV),
              open(os.path.join(work, "level_url.json"), "w"))
    open(os.path.join(work, "specs.txt"), "w").write(" ".join(specs))
    print(len(views), "views planned in", work)


def sheet(gname, views, work, out, title=""):
    from PIL import Image, ImageDraw, ImageFont
    W, H = 960, 540
    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    except OSError:
        f = ImageFont.load_default()
    rows = []
    for v in views:
        ge = os.path.join(work, "ge", v["name"] + ".png")
        ours = os.path.join(work, "ours", "%s_%s.png" % (gname, v["name"]))
        if not (os.path.exists(ge) and os.path.exists(ours)):
            continue
        a = Image.open(ge).convert("RGB").resize((W, H))
        b = Image.open(ours).convert("RGB").resize((W, H))
        r = Image.new("RGB", (W * 2 + 8, H), (20, 20, 20))
        r.paste(a, (0, 0)); r.paste(b, (W + 8, 0))
        d = ImageDraw.Draw(r)
        for x, lab in ((0, "Google Earth"), (W + 8, "Ours")):
            d.rectangle([x, 0, x + 330, 34], fill=(0, 0, 0))
            d.text((x + 8, 5), "%s  %s" % (lab, v.get("label", v["name"])), fill=(255, 255, 255), font=f)
        rows.append(r)
    if not rows:
        print("no pairs"); return
    top = 44 if title else 0
    s = Image.new("RGB", (rows[0].width, top + len(rows) * (H + 8)), (20, 20, 20))
    if title:
        ImageDraw.Draw(s).text((10, 8), title, fill=(255, 255, 255), font=f)
    for i, r in enumerate(rows):
        s.paste(r, (0, top + i * (H + 8)))
    s.save(out, quality=82)
    print("sheet", out, len(rows), "pairs")


# ---- numbers from a straight-down pair (never judge by eye) -------------------------------------------------

def _pair(gname, views, work, vname):
    """Edges of Google Earth's and our straight-down picture of view vname, at GE's size, and metres per pixel."""
    import cv2
    import numpy as np
    g = GROUNDS[gname]
    v = [x for x in views if x["name"] == vname][0]
    if v["t"] >= 3:
        raise SystemExit("%s is not a straight-down view (t < 3)" % vname)
    ge = cv2.imread(os.path.join(work, "ge", vname + ".png"), 0)
    ours = cv2.imread(os.path.join(work, "ours", "%s_%s.png" % (gname, vname)), 0)
    if ge is None or ours is None:
        raise SystemExit("need %s/ge/%s.png and %s/ours/%s_%s.png" % (work, vname, work, gname, vname))
    ours = cv2.resize(ours, (ge.shape[1], ge.shape[0]), interpolation=cv2.INTER_AREA)
    ro = readouts(os.path.join(work, "ge", vname + "_cam.png"))
    cam = ro[0][0] if ro and ro[0][0] is not None else None
    if cam is None:
        print("no camera readout: using the asked range (sizes then only as good as Google Earth's obedience)")
        h = v["d"] + v.get("at", [0, 0, 0])[2]
    else:
        h = cam - g["ge_alt"]
    mpp = 2 * h * math.tan(math.radians(FOV / 2)) / ge.shape[0]
    eg = cv2.Canny(cv2.GaussianBlur(ge, (5, 5), 0), 30, 90)
    eo = cv2.Canny(cv2.GaussianBlur(ours, (3, 3), 0), 40, 120)
    # nothing from Google Earth's own furniture: top bar, tip box, bottom-right buttons
    eg[: int(0.03 * ge.shape[0])] = 0
    return eg, eo, mpp, h


def _stadium_only(e, mpp, radius_m):
    import cv2
    import numpy as np
    m = np.zeros_like(e)
    cv2.circle(m, (e.shape[1] // 2, e.shape[0] // 2), int(radius_m / mpp), 255, -1)
    out = e.copy(); out[m == 0] = 0
    return out


def _search(eg, eo, max_turn, max_shift_px):
    """Turn (deg, ours -> GE, clockwise on the picture) and shift (px) putting our edges on GE's: chamfer."""
    import cv2
    import numpy as np
    H, W = eg.shape
    dt = np.minimum(cv2.distanceTransform(255 - eg, cv2.DIST_L2, 3), 15).astype(np.float32)
    T = max_shift_px
    dtp = cv2.copyMakeBorder(dt, T, T, T, T, cv2.BORDER_CONSTANT, value=15)

    def score(a):
        M = cv2.getRotationMatrix2D((W / 2, H / 2), -a, 1.0)
        e = (cv2.warpAffine(eo, M, (W, H), flags=cv2.INTER_NEAREST) > 0).astype(np.float32)
        r = cv2.matchTemplate(dtp, e, cv2.TM_CCORR) / max(e.sum(), 1)
        y, x = np.unravel_index(r.argmin(), r.shape)
        return float(r.min()), x - T, y - T

    best = None
    for a in np.arange(-max_turn, max_turn + 1e-6, 0.5):
        c, dx, dy = score(a)
        if best is None or c < best[0]:
            best = (c, a, dx, dy)
    for a in np.arange(best[1] - 0.4, best[1] + 0.41, 0.1):
        c, dx, dy = score(a)
        if c < best[0]:
            best = (c, a, dx, dy)
    return best


def register(gname, views, work, vname, max_turn=20.0, max_shift_m=60.0, radius_m=160.0):
    """Where our model sits against Google Earth, straight down: shift east/north (m) and turn (deg).
    Passes at <= 1 m and <= 0.5 deg. Uses only edges within radius_m of the centre (the stadium), so roads and
    houses cannot pull it; check with a second run after fixing that it comes back near zero."""
    eg, eo, mpp, h = _pair(gname, views, work, vname)
    eo = _stadium_only(eo, mpp, radius_m)
    c, a, dx, dy = _search(eg, eo, max_turn, int(max_shift_m / mpp))
    east, north = dx * mpp, -dy * mpp
    ok = abs(east) <= 1.0 and abs(north) <= 1.0 and abs(a) <= 0.5
    edge = abs(dx) >= int(max_shift_m / mpp) - 1 or abs(a) >= max_turn - 0.01
    print("%s %s: camera %.0f m over the turf, %.3f m/px. Ours must move %+.1f m east, %+.1f m north and turn %+.1f deg "
          "(clockwise seen from above) to sit on Google Earth (edge distance %.2f px). %s%s"
          % (gname, vname, h, mpp, east, north, a, c, "PASS" if ok else "FAIL",
             " - at the search limit: widen it or start nearer" if edge else ""))
    if abs(a) > 2:
        print("  a turn over 2 deg usually means the model (or its surroundings) was built in an oval-aligned frame, "
              "not north-up, or the origin's lat/lon is wrong")
    return dict(east_m=round(east, 2), north_m=round(north, 2), turn_deg=round(float(a), 2), ok=ok, mpp=round(mpp, 4))


def outline(gname, views, work, vname, radius_m=160.0):
    """Our edges against Google Earth's, straight down, after register's shift: distance (m) from each of our
    edge pixels to the nearest GE edge, overall and by 30-degree sector from the centre. Lenient over busy areas
    (seat rows, rooftops: a wrong line can land near some edge), so read it with the overlay it writes."""
    import cv2
    import numpy as np
    eg, eo, mpp, h = _pair(gname, views, work, vname)
    eo = _stadium_only(eo, mpp, radius_m)
    c, a, dx, dy = _search(eg, eo, 20.0, int(60.0 / mpp))
    H, W = eg.shape
    M = cv2.getRotationMatrix2D((W / 2, H / 2), -a, 1.0); M[0, 2] += dx; M[1, 2] += dy
    eo2 = cv2.warpAffine(eo, M, (W, H), flags=cv2.INTER_NEAREST)
    dt = cv2.distanceTransform(255 - eg, cv2.DIST_L2, 5) * mpp
    ys, xs = np.nonzero(eo2)
    d = dt[ys, xs]
    brg = (np.degrees(np.arctan2(xs - W / 2, -(ys - H / 2))) + 360) % 360
    res = dict(ground=gname, view=vname, shift_east_m=round(dx * mpp, 2), shift_north_m=round(-dy * mpp, 2),
               turn_deg=round(float(a), 2), median_m=round(float(np.median(d)), 2),
               within_1m=round(float((d <= 1).mean()), 3), within_2m=round(float((d <= 2).mean()), 3),
               within_4m=round(float((d <= 4).mean()), 3), p90_m=round(float(np.percentile(d, 90)), 2), sectors={})
    for s0 in range(0, 360, 30):
        k = (brg >= s0) & (brg < s0 + 30)
        if k.sum() > 50:
            res["sectors"]["%d-%d" % (s0, s0 + 30)] = dict(median_m=round(float(np.median(d[k])), 2),
                                                          within_2m=round(float((d[k] <= 2).mean()), 3))
    print(json.dumps(res, indent=1))
    img = cv2.cvtColor(cv2.imread(os.path.join(work, "ge", vname + ".png"), 0), cv2.COLOR_GRAY2BGR)
    img[ys[d <= 2], xs[d <= 2]] = (0, 255, 255)
    img[ys[d > 2], xs[d > 2]] = (255, 0, 255)
    out = os.path.join(work, "%s_%s_outline.jpg" % (gname, vname))
    cv2.imwrite(out, img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    json.dump(res, open(out[:-4] + ".json", "w"), indent=1)
    print("overlay (yellow = ours within 2 m of a GE edge, magenta = further):", out)
    return res


if __name__ == "__main__":
    cmd, gname, vf, work = sys.argv[1:5]
    views = json.load(open(vf))
    if gname not in GROUNDS:
        raise SystemExit("%s is not in tools/grounds/ge/grounds.json" % gname)
    if cmd == "plan":
        plan(gname, views, work)
    elif cmd == "level":
        level(gname, work)
    elif cmd == "register":
        register(gname, views, work, sys.argv[5])
    elif cmd == "outline":
        outline(gname, views, work, sys.argv[5])
    else:
        sheet(gname, views, work, sys.argv[5], sys.argv[6] if len(sys.argv) > 6 else "")
