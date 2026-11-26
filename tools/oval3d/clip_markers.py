#!/usr/bin/env python3
"""The moments inside each ball-handling clip, read off the motion itself (row 198).

Input: the bone dump of tools/oval3d/dump_clip_bones.gd (60 Hz, figure space, +z his front).
Output: assets/oval3d/clip_moments.json, which Oval3DAnim reads to play a kick, handball or mark
so that its contact frame lands on the director's touch of the ball.

  godot --headless --path . --script tools/oval3d/dump_clip_bones.gd -- /tmp/bones.json
  python3 tools/oval3d/clip_markers.py /tmp/bones.json assets/oval3d/clip_moments.json

Per clip:
  kind      kick | handball | mark
  contact   s: kick, the kicking foot at its fastest on the way up (the boot meets the ball);
            handball, the palms closest (the fist through the ball); mark, the palms closest
            while the hands are at their highest stretch (the ball into them)
  limb      the bone that meets the ball (ball_l / ball_r for a foot, hand_l / hand_r)
  at        [x, y, z] where the ball is at contact, figure space (a kick: the top of the boot,
            BALL_ON_BOOT above the toe bone; a handball or mark: between the palms)
  start     s: where the clip can begin with the ball in his hands (palms together, before the
            contact); a mark's start is the run-in before the hands go up
  end       s: the follow-through done (the clip hands back to the run or stand)
  hips      [x, z] of the hips at contact, figure space
  speed     m/s the hips cover from start to contact (the pace the clip is run at)
"""
import json
import math
import sys

BALL_ON_BOOT = 0.09   # m: the ball's centre above the toe bone at contact (boot top + ball radius)
HELD_GAP = 0.32       # m: palms closer than this hold the ball
FOLLOW = 0.45         # s after contact the follow-through runs before he can run on

# Which clips play which move. Picked by eye from the side and front stills
# (docs/research/ANIMATION_AUDIT_2026-11-22.md): each one starts with the ball in both hands.
CLIPS = {
    "kick_on_run_03": "kick",        # right foot, on the run
    "kick_on_run_02_run": "kick",    # left foot, on the run
    "drop_punt_02": "kick",          # right foot, from a walk-in (set up, after a mark)
    "handball_on_run_01": "handball",
    "chest_mark_02": "mark",
    "overhead_mark_01": "mark",
}


def dist(a, b):
    return math.dist(a, b)


def mid(a, b):
    return [(x + y) * 0.5 for x, y in zip(a, b)]


def kick(F, hz):
    best = (0.0, None, 0)
    for limb in ("ball_l", "ball_r"):
        for i in range(1, len(F)):
            if F[i][limb][1] < 0.15:
                continue
            s = dist(F[i][limb], F[i - 1][limb]) * hz
            if s > best[0]:
                best = (s, limb, i)
    _, limb, c = best
    start = 0
    for i in range(c, -1, -1):
        if dist(F[i]["hand_l"], F[i]["hand_r"]) <= HELD_GAP:
            start = i
            break
    p = F[c][limb]
    return c, limb, [p[0], p[1] + BALL_ON_BOOT, p[2]], start


def handball(F, hz):
    gaps = [dist(f["hand_l"], f["hand_r"]) for f in F]
    c = min(range(len(F)), key=lambda i: gaps[i])
    # The punching hand is the one moving faster into the ball.
    sp = {h: dist(F[c][h], F[c - 1][h]) * hz for h in ("hand_l", "hand_r")}
    limb = max(sp, key=sp.get)
    return c, limb, mid(F[c]["hand_l"], F[c]["hand_r"]), 0


def mark(F, hz):
    mids = [mid(f["hand_l"], f["hand_r"])[1] for f in F]
    top = max(mids)
    pool = [i for i in range(len(F)) if mids[i] >= 0.8 * top]
    c = min(pool, key=lambda i: dist(F[i]["hand_l"], F[i]["hand_r"]))
    return c, "hand_l", mid(F[c]["hand_l"], F[c]["hand_r"]), 0


def main():
    src, out = sys.argv[1], sys.argv[2]
    data = json.load(open(src))
    res = {}
    for name, kind in CLIPS.items():
        clip = data[name]
        F, hz = clip["frames"], clip["hz"]
        c, limb, at, s = {"kick": kick, "handball": handball, "mark": mark}[kind](F, hz)
        h0, h1 = F[s]["pelvis"], F[c]["pelvis"]
        secs = max((c - s) / hz, 1e-3)
        res[name] = {
            "kind": kind,
            "contact": round(c / hz, 3),
            "limb": limb,
            "at": [round(v, 3) for v in at],
            "start": round(s / hz, 3),
            "end": round(min(clip["len"], c / hz + FOLLOW), 3),
            "hips": [round(h1[0], 3), round(h1[2], 3)],
            "speed": round(math.dist((h0[0], h0[2]), (h1[0], h1[2])) / secs, 2),
        }
        print(name, res[name])
    with open(out, "w") as f:
        json.dump(res, f, indent=1, sort_keys=True)
        f.write("\n")


if __name__ == "__main__":
    main()
