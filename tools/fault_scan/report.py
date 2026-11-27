"""The fault scan's report (tools/fault_scan/README.md): each finding's camera shot with the fault ringed, the
shots as JPEGs, and the ground's defect list as Markdown.

    python3 tools/fault_scan/report.py <analyse_out_dir> <shots_dir> <report_dir>

Writes <report_dir>/<slug>.md and <report_dir>/<slug>/<view>.jpg.
"""
import json, math, os, sys

import numpy as np
from PIL import Image, ImageDraw

NAMES = {
    "backwards_text": "Words on a sign read backwards",
    "mirrored_text": "Printed texture drawn mirror-image",
    "sign_back_mirrored": "Sign reads backwards from behind",
    "stretched_texture": "Texture stretched or squashed",
    "dull_sign": "Sign colours dimmed",
    "floating": "Floating objects",
    "short_leg": "Legs or posts short of the floor",
    "seat_colours_random": "Seat colours random",
    "seat_tipped": "Seats tipped over",
    "seat_huge": "Seats far too big",
    "seat_backwards": "Seats facing away from the field",
    "seat_off_tread": "Seats off their treads",
    "seat_buried": "Seats with the stand through them",
    "seat_in_fence": "Seats inside the fence",
    "seat_far_near": "Far-seat cards up close",
    "leg_huge": "Seat legs as huge slabs",
    "leg_no_seat": "Seat legs with no seat",
    "leg_over_field": "Seat legs over the field",
    "sky_gap": "Seats open to the sky through a gap",
    "tree_on_roof": "Trees on roofs",
    "tree_floating": "Trees floating",
    "frame_mirrored": "Whole ground mirror-image",
    "model_offset": "Stadium off its real position",
    "stadium_on_road": "Stadium on a road",
    "building_on_road": "Building on a road",
    "missing_bridge": "Bridge or walkway missing",
    "missing_building": "Building missing",
    "solid_shelter": "Open shelter built solid",
    "broken_outline": "Building outline broken",
    "jagged_outline": "Building outline jagged",
    "generic_facades": "Made-up windows",
    "generic_trees": "Stock trees",
    "on_arena": "Something on the arena",
}


def cam(line):
    w = line.split()
    return {"name": w[0], "eye": np.array([float(w[1]), float(w[2]), float(w[3])]), "facing": float(w[4]),
            "looking": float(w[5]), "fov": float(w[6]) if w[6] != "ortho" else None}


def project(c, p, W, H):
    yaw = -math.radians(c["facing"])
    pitch = math.radians(c["looking"])
    cy, sy, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    R = Ry @ Rx
    q = R.T @ (np.asarray(p, float) - c["eye"])
    if q[2] > -0.1:
        return None
    t = math.tan(math.radians(c["fov"]) / 2)
    x = q[0] / (-q[2] * t * (W / H))
    y = q[1] / (-q[2] * t)
    return ((x + 1) / 2 * W, (1 - y) / 2 * H)


def main():
    src, shots, rep = sys.argv[1], sys.argv[2], sys.argv[3]
    F = json.load(open(os.path.join(src, "findings.json")))
    slug = F["slug"]
    views = {}
    for line in open(os.path.join(src, "views.txt")):
        if line.strip() and not line.startswith("#"):
            c = cam(line)
            views[c["name"]] = (c, line.strip())
    od = os.path.join(rep, slug)
    os.makedirs(od, exist_ok=True)
    # every shot as a JPEG; a finding's shots with the fault ringed
    target = {}
    for f in F["findings"]:
        for v in f.get("views", []):
            target[v["name"]] = v["target"]
    for name, (c, line) in views.items():
        fp = os.path.join(shots, name + ".png")
        if not os.path.exists(fp):
            continue
        im = Image.open(fp).convert("RGB")
        if name in target and c["fov"]:
            pt = project(c, target[name], im.width, im.height)
            if pt:
                d = ImageDraw.Draw(im)
                r = max(18, im.height // 18)
                for k in range(3):
                    d.ellipse([pt[0] - r - k, pt[1] - r - k, pt[0] + r + k, pt[1] + r + k], outline=(255, 30, 30))
        im.save(os.path.join(od, name + ".jpg"), quality=85)
    pr = os.path.join(src, "prints")
    if os.path.isdir(pr):
        for fn in os.listdir(pr):
            Image.open(os.path.join(pr, fn)).convert("RGB").save(os.path.join(od, fn.replace(".png", ".jpg")), quality=90)
    # the Markdown list
    L = ["# %s: machine fault scan" % F["ground"], "",
         "Every position is in the ground inspector's coordinates (what its C key copies). Each screenshot has the "
         "fault ringed in red where the scan could place it.", ""]
    st = F["stats"]
    L.append("Scan facts: %s seats, %s textured surfaces, %s seat legs; OpenStreetMap %s." % (
        st.get("seats", 0), st.get("textured_surfaces", 0), st.get("legs", 0),
        "not available" if st.get("osm") == "missing" else "read"))
    if st.get("check_errors"):
        L.append("Checks that failed to run: " + "; ".join(st["check_errors"]))
    L.append("")
    for f in F["findings"]:
        L.append("## %d. %s" % (f["id"], f["title"]))
        L.append("")
        L.append("- Where: %s" % ("whole ground" if f["where"] == [0, 0, 0] else "x %.1f  y %.1f  z %.1f" % tuple(f["where"])))
        L.append("- What: %s" % f["detail"])
        L.append("- Likely cause: %s" % f["cause"])
        for p in f.get("places", [])[:12]:
            L.append("  - %s: %s" % (p["where"], p["note"]))
        for v in f.get("views", []):
            L.append("- Screenshot from %s: ![](%s/%s.jpg)" % (v["where"], slug, v["name"]))
        if f.get("print"):
            L.append("- The board as it reads in the game: ![](%s/%s)" % (slug, f["print"].replace(".png", ".jpg")))
        L.append("")
    open(os.path.join(rep, slug + ".md"), "w").write("\n".join(L) + "\n")
    print("report: %d findings, %d shots" % (len(F["findings"]), len(views)))


if __name__ == "__main__":
    main()
