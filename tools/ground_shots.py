#!/usr/bin/env python3
"""Ground shots: flag every ground whose fixed-camera captures changed.

    python3 tools/ground_shots.py BASELINE_DIR CURRENT_DIR OUT_DIR \
        [--changed-files FILE] [--title TEXT] [--expect N]

BASELINE_DIR and CURRENT_DIR hold tools/visual/capture_grounds3d.gd output
(<slug>_<shot>.png, a few fixed cameras per ground). Each pair of shots is
compared pixel by pixel. A pixel counts as changed when one of its channels
moved by more than PIXEL_DELTA (out of 255), which ignores the film grain and
grass sway that move from run to run; a shot counts as changed when more than
SHOT_SHARE of its pixels did.

OUT_DIR gets:
  report.md   the summary (also fit for $GITHUB_STEP_SUMMARY)
  report.json the same as data
  diff/<slug>.png  for each changed ground: baseline, now and the changed
                   pixels in red, one row per shot

--changed-files names a file listing the paths that changed between the two
captures (git diff --name-only). A ground whose own folder (assets/grounds/<slug>)
changed is "expected"; a ground that changed with nothing of its own touched is
"unexpected", the quiet break this check is for.

--expect N: fail when fewer than N grounds were captured (a ground that stopped
loading leaves no shots).

Exit status: 0 when nothing broke, 1 when a ground went missing, fewer grounds
than --expect were captured, or a shot is unreadable. Changed looks alone are
information and exit 0.
"""
import argparse
import json
import os
import re
import sys

from PIL import Image, ImageChops, ImageDraw

PIXEL_DELTA = 24
SHOT_SHARE = 0.005
CELL_W = 480
LABEL_H = 22
BG = (18, 18, 18)
INK = (235, 230, 220)
SHOT_RE = re.compile(r"^(?P<slug>.+)_(?P<shot>[a-z0-9]+)\.png$")


def shots_in(folder):
    """{slug: {shot: path}} for every capture in a folder."""
    out = {}
    if not folder or not os.path.isdir(folder):
        return out
    for name in sorted(os.listdir(folder)):
        m = SHOT_RE.match(name)
        if not m:
            continue
        slug, shot = m.group("slug"), m.group("shot")
        out.setdefault(slug, {})[shot] = os.path.join(folder, name)
    return out


def compare(a_path, b_path):
    """(changed share 0..1, mask image) for two captures of one shot."""
    a = Image.open(a_path).convert("RGB")
    b = Image.open(b_path).convert("RGB")
    if a.size != b.size:
        return 1.0, Image.new("L", b.size, 255)
    diff = ImageChops.difference(a, b)
    r, g, bl = diff.split()
    peak = ImageChops.lighter(ImageChops.lighter(r, g), bl)
    mask = peak.point(lambda v: 255 if v > PIXEL_DELTA else 0)
    changed = mask.histogram()[255]
    return changed / float(a.size[0] * a.size[1]), mask


def fit(img, w):
    h = max(1, round(img.size[1] * w / img.size[0]))
    return img.resize((w, h), Image.LANCZOS)


def diff_sheet(slug, rows, path):
    """One row per shot: baseline | now | changed pixels in red over a dimmed now."""
    tiles = []
    for shot, a_path, b_path, share, mask in rows:
        a = fit(Image.open(a_path).convert("RGB"), CELL_W)
        b = fit(Image.open(b_path).convert("RGB"), CELL_W)
        m = mask.resize(b.size)
        heat = Image.blend(b, Image.new("RGB", b.size, (0, 0, 0)), 0.6)
        heat.paste(Image.new("RGB", b.size, (255, 40, 40)), (0, 0), m)
        tiles.append((shot, share, a, b, heat))
    cell_h = max(t[2].size[1] for t in tiles)
    sheet = Image.new("RGB", (CELL_W * 3, (cell_h + LABEL_H) * len(tiles) + LABEL_H), BG)
    draw = ImageDraw.Draw(sheet)
    for i, head in enumerate(["baseline", "now", "changed pixels"]):
        draw.text((i * CELL_W + 6, 4), head, fill=INK)
    y = LABEL_H
    for shot, share, a, b, heat in tiles:
        draw.text((6, y + 4), "%s %s: %.1f%% of pixels changed" % (slug, shot, share * 100.0), fill=INK)
        y += LABEL_H
        sheet.paste(a, (0, y))
        sheet.paste(b, (CELL_W, y))
        sheet.paste(heat, (CELL_W * 2, y))
        y += cell_h
    sheet.save(path)


def own_files_changed(slug, changed_files):
    prefix = "assets/grounds/%s/" % slug
    return any(f.startswith(prefix) for f in changed_files)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("baseline")
    ap.add_argument("current")
    ap.add_argument("out")
    ap.add_argument("--changed-files", default="")
    ap.add_argument("--title", default="Ground shots")
    ap.add_argument("--expect", type=int, default=0)
    args = ap.parse_args()

    base = shots_in(args.baseline)
    now = shots_in(args.current)
    changed_files = []
    if args.changed_files and os.path.isfile(args.changed_files):
        with open(args.changed_files, encoding="utf-8") as f:
            changed_files = [l.strip() for l in f if l.strip()]
    os.makedirs(os.path.join(args.out, "diff"), exist_ok=True)

    result = {"baseline": bool(base), "grounds": {}, "missing": [], "new": [], "unreadable": []}
    for slug in sorted(set(base) | set(now)):
        if slug not in now:
            result["missing"].append(slug)
            continue
        if slug not in base:
            result["new"].append(slug)
            continue
        rows = []
        worst = 0.0
        for shot in sorted(now[slug]):
            if shot not in base[slug]:
                continue
            try:
                share, mask = compare(base[slug][shot], now[slug][shot])
            except OSError as e:
                result["unreadable"].append("%s_%s: %s" % (slug, shot, e))
                continue
            worst = max(worst, share)
            if share > SHOT_SHARE:
                rows.append((shot, base[slug][shot], now[slug][shot], share, mask))
        entry = {"worst_share": round(worst, 5), "changed_shots": [r[0] for r in rows]}
        if rows:
            entry["own_files_changed"] = own_files_changed(slug, changed_files)
            sheet = os.path.join(args.out, "diff", "%s.png" % slug)
            diff_sheet(slug, rows, sheet)
            entry["sheet"] = os.path.relpath(sheet, args.out)
        result["grounds"][slug] = entry

    changed = {s: e for s, e in result["grounds"].items() if e["changed_shots"]}
    unexpected = sorted(s for s, e in changed.items() if not e.get("own_files_changed"))
    expected = sorted(s for s, e in changed.items() if e.get("own_files_changed"))
    result["changed"] = sorted(changed)
    result["unexpected"] = unexpected
    result["captured"] = len(now)
    too_few = args.expect and len(now) < args.expect
    broke = bool(result["missing"] or result["unreadable"] or too_few)
    result["broke"] = broke

    lines = ["## %s" % args.title, ""]
    if not base:
        lines.append("No baseline to compare with yet: these %d grounds are the first one." % len(now))
    else:
        lines.append("%d grounds captured, %d compared. %d look the same, %d changed."
                     % (len(now), len(result["grounds"]), len(result["grounds"]) - len(changed), len(changed)))
    lines.append("")
    if result["missing"]:
        lines.append("**No longer captured (failed to load?):** " + ", ".join(result["missing"]))
    if too_few:
        lines.append("**Only %d grounds captured; expected at least %d.**" % (len(now), args.expect))
    if result["unreadable"]:
        lines.append("**Unreadable shots:** " + "; ".join(result["unreadable"]))
    if unexpected:
        lines.append("**Changed with none of its own files touched (check these):** "
                     + ", ".join(unexpected))
    if expected:
        lines.append("**Changed along with its own model or textures:** " + ", ".join(expected))
    if result["new"]:
        lines.append("**New grounds (no baseline yet):** " + ", ".join(result["new"]))
    if changed:
        lines += ["", "| Ground | Shots changed | Most changed | Own files touched |", "|---|---|---|---|"]
        for slug in sorted(changed, key=lambda s: -changed[s]["worst_share"]):
            e = changed[slug]
            lines.append("| %s | %s | %.1f%% | %s |" % (slug, ", ".join(e["changed_shots"]),
                                                       e["worst_share"] * 100.0,
                                                       "yes" if e.get("own_files_changed") else "**no**"))
        lines += ["", "Each changed ground has a sheet in the run's artifact: `diff/<ground>.png` "
                  "(baseline, now, changed pixels in red)."]
    lines.append("")
    lines.append("A shot counts as changed when over %.1f%% of its pixels moved by more than %d/255."
                 % (SHOT_SHARE * 100.0, PIXEL_DELTA))
    with open(os.path.join(args.out, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(args.out, "report.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1, sort_keys=True)
    print("\n".join(lines))
    return 1 if broke else 0


if __name__ == "__main__":
    sys.exit(main())
