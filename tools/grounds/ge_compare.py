"""Google Earth side-by-sides for a ground (the MCG standard's gate, docs/MCG_STANDARD.md), kept in the repo.

  python3 tools/grounds/ge_compare.py plan  <ground> <views.json> <workdir>   # GE urls + our camera specs
  node    tools/grounds/ge_shoot.js <workdir> --level                         # once per ground: GE's turf height,
  python3 tools/grounds/ge_compare.py level <ground> <views.json> <workdir>   #   read back: set GROUNDS ge_alt to it
  node    tools/grounds/ge_shoot.js <workdir>                                 # Google Earth shots (Playwright)
  python3 tools/grounds/ge_compare.py plan  <ground> <views.json> <workdir>   # again: ours where GE's camera really was
  godot --path . --rendering-method mobile --script tools/visual/preinspect_look.gd -- <workdir>/ours <slug> $(cat <workdir>/specs.txt)
  python3 tools/grounds/ge_compare.py sheet <ground> <views.json> <workdir> <out.jpg> [title]

A view is {"name", "h" heading deg, "t" tilt deg (0 = straight down), "d" range m, "at" [east, north, up] m from
the field centre}. Our camera is the same: target - d * (sin t sin h, sin t cos h, -cos t) in (east, north, up),
then through the match's fit (GroundModels.fit_transform) into match metres. Google Earth lifts a camera it thinks
too low (keeping its spot and tilt), so once the shots exist, plan reads where each one really was (the status bar
ge_shoot.js saves beside each shot, read with tesseract) and lifts ours the same; without tesseract it warns and
leaves ours where asked, and a low view's pair is then not to be trusted for sizes."""
import json, math, os, sys

UNDER_TURF = 0.1
# Per ground: the model origin's lat/lon (model x east, -z north), Google Earth's field level (m above sea level)
# and the match fit (GroundModels.FIT: centre x, centre z, floor y, long axis deg, half length, half width).
# ge_alt is the height Google Earth itself gives the turf, read off its status bar with the mouse on the grass
# (`node tools/grounds/ge_shoot.js <workdir> --level`, after `plan`), never a map's elevation: Adelaide's turf is
# 26 m in Google Earth, and the 40 m first used here put every Google Earth camera 14 m higher over the field
# than ours (2026-11-22). The MCG's turf reads 8 m.
GROUNDS = {
    "adelaide": {"lat": -34.915489777922076, "lon": 138.59627692467532, "ge_alt": 26.0,
                 "fit": [-0.4, 1.37, 0.0, -102.0, 91.36, 65.7]},
    # The Gabba: origin solved from OSM way 4049692 against tools/grounds/gabba/osm/geo.json (2 cm rms).
    "gabba": {"lat": -27.4858478, "lon": 153.0380888, "ge_alt": 22.0,
              "fit": [2.47, 3.47, 0.0, 175.0, 86.88, 73.71]},
}
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
        # Straight down: nudge the camera 3 degrees south so north stays up the picture (preinspect_look
        # only keeps world up as the picture's up while the view is under 87.4 degrees from vertical).
        if v["t"] < 3:
            cam = (cam[0], cam[1] - 0.05 * d, cam[2])
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
        specs.append("%s:%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.1f" % ((v["name"],) + pc + pt + (v.get("fov", FOV),)))
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


if __name__ == "__main__":
    cmd, gname, vf, work = sys.argv[1:5]
    views = json.load(open(vf))
    if cmd == "plan":
        plan(gname, views, work)
    elif cmd == "level":
        level(gname, work)
    else:
        sheet(gname, views, work, sys.argv[5], sys.argv[6] if len(sys.argv) > 6 else "")
