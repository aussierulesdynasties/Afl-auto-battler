"""Google Earth side-by-sides for a ground (the MCG standard's gate, docs/MCG_STANDARD.md). A copy of the Adelaide rebuild's tools/grounds/ge_compare.py (PR #2010) with GMHBA and Bellerive added; fold the copies together once all are on main.

  python3 tools/grounds/norwood/qa/ge_compare.py plan  <ground> <views.json> <workdir>   # GE urls + our camera specs
  node    tools/grounds/norwood/qa/ge_shoot.js <workdir>                                 # Google Earth shots (Playwright)
  godot --path . --rendering-method mobile --script tools/visual/preinspect_look.gd -- <workdir>/ours <slug> $(cat <workdir>/specs.txt)
  python3 tools/grounds/norwood/qa/ge_compare.py sheet <ground> <views.json> <workdir> <out.jpg> [title]

A view is {"name", "h" heading deg, "t" tilt deg (0 = straight down), "d" range m, "at" [east, north, up] m from
the field centre}. Our camera is the same: target - d * (sin t sin h, sin t cos h, -cos t) in (east, north, up),
then through the match's fit (GroundModels.fit_transform) into match metres. Looks only."""
import json, math, os, sys

UNDER_TURF = 0.1
# Per ground: the model origin's lat/lon (model x east, -z north), Google Earth's field level (m above sea level)
# and the match fit (GroundModels.FIT: centre x, centre z, floor y, long axis deg, half length, half width).
GROUNDS = {
    "adelaide": {"lat": -34.915489777922076, "lon": 138.59627692467532, "ge_alt": 40.0,
                 "fit": [-0.4, 1.37, 0.0, -102.0, 91.36, 65.7]},
    # GMHBA: the model's origin from 7 Google Earth wall-foot points (tools/grounds/gmhba/jss_roof/measured.md).
    "gmhba": {"lat": -38.1579976, "lon": 144.3546774, "ge_alt": 20.0,
              "fit": [-8.89, 11.85, 0.02, -69.8, 94.3, 66.01]},
    # Bellerive: the model's origin is the centre of the OSM pitch outline (tools/grounds/bellerive/work/geo.py);
    # Google Earth's field level is 10 m (work/dz.txt).
    # Norwood: the model's origin is the centre circle (Google Earth's top-down mosaic); field level 50 m.
    "norwood": {"lat": -34.919825, "lon": 138.630446, "ge_alt": 50.0,
                "fit": [2.14, 0.49, 0.0, 84.56, 88.71, 58.4]},
    "bellerive": {"lat": -42.8773092, "lon": 147.3737365, "ge_alt": 10.0,
                  "fit": [0.31, -0.64, -0.02, 68.7, 86.9, 66.77]},
}
FOV = 25.6   # Google Earth's 35 degrees over the 1000 px window, cropped to 720 rows (ge_shoot.js)


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
                     "https://earth.google.com/web/@%.7f,%.7f,%.1fa,%.1fd,35y,%.1fh,%.1ft,0r" % (lat, lon, g["ge_alt"] + u, d, v["h"], v["t"])])
        dirv = (math.sin(t) * math.sin(h), math.sin(t) * math.cos(h), -math.cos(t))
        cam = (e - d * dirv[0], n - d * dirv[1], u - d * dirv[2])
        # Straight down: nudge the camera 3 degrees south so north stays up the picture (preinspect_look
        # only keeps world up as the picture's up while the view is under 87.4 degrees from vertical).
        if v["t"] < 3:
            cam = (cam[0], cam[1] - 0.05 * d, cam[2])
        pc = to_match(g, (cam[0], cam[2], -cam[1]))
        pt = to_match(g, (e, u, -n))
        specs.append("%s:%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.1f" % ((v["name"],) + pc + pt + (v.get("fov", FOV),)))
    json.dump(urls, open(os.path.join(work, "urls.json"), "w"), indent=1)
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
    else:
        sheet(gname, views, work, sys.argv[5], sys.argv[6] if len(sys.argv) > 6 else "")
