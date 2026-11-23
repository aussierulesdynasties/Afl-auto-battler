"""Alice Springs' gums, as low-poly geometry: a trunk that forks into limbs and an open crown of separate
leaf clumps with sky between them (a gum's crown is never a ball). Two barks: the white ghost gum and the
grey-brown river red gum and bloodwood; the leaves a dull olive grey-green, darker underneath.

A tree within NEAR_R of the oval gets 4 to 5 limbs, a twig off each and 2 to 3 leaf clusters at every end
(about 250 triangles); to MID_R 3 limbs and 2 clusters each (about 70); past MID_R it is two crossed cards
showing a picture of one of our own near gums (impostor.py, tex/gum_far.png). Placed from Google Earth's
straight-down views (canopy.py): each tree's crown as wide as its canopy there.
"""
import json
import math
import os

import numpy as np

from bldg import Batch

NEAR_R, MID_R = 180.0, 300.0
# impostor.py's four pictures: (the tree's height, the square picture's side), metres
CARD = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tex", "gum_far.json")))
LEAF = [(118, 128, 92), (130, 136, 98), (108, 122, 88), (138, 140, 104), (122, 134, 100)]
BARK = {"ghost": (214, 208, 196), "red": (128, 112, 98)}


def _ico():
    t = (1 + 5 ** 0.5) / 2
    v = np.array([(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
                  (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)], float)
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    f = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6),
         (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10),
         (8, 6, 7), (9, 8, 1)]
    return v, f


ICO_V, ICO_F = _ico()


class Forest:
    def __init__(self):
        self.leaf = Batch()
        self.bark = Batch()
        self.far = Batch()
        self.n = 0

    def add(self, e, n, y, h, rad, seed, r):
        """A gum: one or two stems leaning off true, forking at a third of its height into limbs that run
        up and out to the crown's edge; foliage hangs in separate clusters at the limb and twig ends, with
        sky between them (a gum's crown is open and broad, never a ball)."""
        rng = np.random.default_rng(seed)
        self.n += 1
        if r >= MID_R:
            return self._card(e, n, y, h, rad, rng)
        near = r < NEAR_R
        kind = "ghost" if rng.random() < 0.3 else "red"
        f = rng.uniform(0.9, 1.06)
        bark = tuple(int(min(255, c * f)) for c in BARK[kind]) + (255,)
        base = np.array([e, y, -n])
        fork = h * rng.uniform(0.25, 0.4)
        tr = max(0.15, rad * 0.07)
        sides = 5 if near else 4
        stems = 2 if (near and rng.random() < 0.25) else 1
        crown_y = y + h - rad * 0.45            # the crown's middle: broad and flattish, its top at h
        tips = []
        for s_ in range(stems):
            off = np.array([rng.normal(0, 0.25), 0, rng.normal(0, 0.25)]) * (tr * 3 if stems > 1 else 0)
            lean = np.array([rng.normal(0, 0.1), 0, rng.normal(0, 0.1)]) * fork
            b0 = base + off
            mid = b0 + np.array([0, fork * 0.5, 0]) + lean * 0.35
            top = b0 + np.array([0, fork, 0]) + lean
            k = 1.0 if stems == 1 else 0.75
            if near:
                self._limb(b0 - np.array([0, 0.3, 0]), mid, tr * 1.2 * k, tr * k, bark, sides)
                self._limb(mid, top, tr * k, tr * 0.85 * k, bark, sides)
            else:
                self._limb(b0 - np.array([0, 0.3, 0]), top, tr * 1.2 * k, tr * 0.85 * k, bark, sides)
            nl = (int(rng.integers(4, 6)) if near else 3) // stems + (1 if stems > 1 else 0)
            a0 = rng.uniform(0, 2 * math.pi)
            for i in range(nl):
                a = a0 + 2 * math.pi * i / nl + rng.normal(0, 0.35)
                out = rad * rng.uniform(0.45, 0.8)     # with the clusters round each end the leaf reaches the canopy edge
                end = np.array([e + math.cos(a) * out, crown_y + rad * rng.uniform(-0.15, 0.35), -n + math.sin(a) * out])
                knee = top + (end - top) * 0.45 + np.array([0, rad * 0.12, 0])
                if near:
                    self._limb(top, knee, tr * 0.7, tr * 0.5, bark, 4)
                    self._limb(knee, end, tr * 0.5, tr * 0.22, bark, 3)
                else:
                    self._limb(top, end, tr * 0.6, tr * 0.25, bark, 3)
                tips.append((end, a))
                if near:                         # a twig off each limb, its own cluster
                    a2 = a + rng.choice([-1, 1]) * rng.uniform(0.5, 0.9)
                    t2 = knee + np.array([math.cos(a2) * rad * 0.35, rad * rng.uniform(0.15, 0.4), math.sin(a2) * rad * 0.35])
                    self._limb(knee, t2, tr * 0.35, tr * 0.15, bark, 3)
                    tips.append((t2, a2))
        # Clusters big enough to close the crown to Google Earth's fill (QA 2026-11-22: at 0.26-0.36 of the
        # crown's radius the gums read as lollipops on sticks against Google Earth's wall of canopy); gaps
        # stay inside each spray (the leaf atlas is a third leaf), so the crown is still open up close.
        self._cap(e, n, y + h - rad * 0.6, rad, rng)
        for end, a in tips:
            nc = 3 if near else 2
            for k in range(nc):
                c = end + np.array([rng.normal(0, rad * 0.2), rad * rng.uniform(-0.12, 0.18), rng.normal(0, rad * 0.2)])
                s = rad * (rng.uniform(0.36, 0.46) if near else rng.uniform(0.5, 0.6))
                col = LEAF[int(rng.integers(len(LEAF)))]
                self._clump(c, s, col, rng, np.array([e, crown_y, -n]))

    def _card(self, e, n, y, h, rad, rng):
        """A far gum: two crossed upright cards showing one of impostor.py's four gums side on, and over them
        a level card showing its crown from above (for the high cameras)."""
        k = int(rng.integers(4))
        H, w, wt = CARD[k]
        sc = h / H                                   # the picture's tree scaled to this tree's height
        fit = float(np.clip(rad / (0.5 * wt * sc / 1.03), 0.8, 1.25))
        half = w * sc / 2 * fit
        top = y + w * sc
        yaw = rng.uniform(0, math.pi)
        f = rng.uniform(0.88, 1.0)
        tint = tuple(int(255 * f * c) for c in (1.0, 1.0, 0.98)) + (255,)
        b = self.far
        u0, u1 = k / 4.0, (k + 1) / 4.0
        for j in range(2):
            a = yaw + j * math.pi / 2
            dx, dz = math.cos(a) * half, math.sin(a) * half
            q = [(e - dx, y - 0.2, -n - dz), (e + dx, y - 0.2, -n + dz), (e + dx, top, -n + dz), (e - dx, top, -n - dz)]
            b.P += q
            b.N += [(0.0, 1.0, 0.0)] * 4            # lit as a crown's top is, whichever way the card faces
            b.C += [tint] * 4
            b.UV += [(u0, 0.5), (u1, 0.5), (u1, 0.0), (u0, 0.0)]
            k0 = b.n
            b.F += [(k0, k0 + 1, k0 + 2), (k0, k0 + 2, k0 + 3), (k0, k0 + 2, k0 + 1), (k0, k0 + 3, k0 + 2)]
            b.n += 4
        ht = wt * sc / 2 * fit
        yc = y + h * 0.82
        c, s_ = math.cos(yaw), math.sin(yaw)
        corners = [(-ht, -ht), (ht, -ht), (ht, ht), (-ht, ht)]      # picture west-east, north-south
        b.P += [(e + c * x - s_ * z, yc, -n + s_ * x + c * z) for x, z in corners]
        b.N += [(0.0, 1.0, 0.0)] * 4
        b.C += [tint] * 4
        b.UV += [(u0, 0.5), (u1, 0.5), (u1, 1.0), (u0, 1.0)]
        k0 = b.n
        b.F += [(k0, k0 + 2, k0 + 1), (k0, k0 + 3, k0 + 2)]          # facing up
        b.n += 4

    def _cap(self, e, n, yc, rad, rng):
        """Inside a near gum's crown, a level card of impostor.py's picture of a gum from straight above (the
        far atlas' bottom row), as wide as the crown. Edge on from the ground, so the clusters make the crown
        there; from above it closes the gaps the sprays leave, as Google Earth's top-down views show the
        crowns (QA 2026-11-23: near crowns from above read as a third as dense as Google Earth's)."""
        k = int(rng.integers(4))
        u0, u1 = k / 4.0, (k + 1) / 4.0
        ht = rad * 1.03
        yaw = rng.uniform(0, 2 * math.pi)
        c, s_ = math.cos(yaw), math.sin(yaw)
        f = rng.uniform(0.88, 1.0)
        tint = tuple(int(255 * f * q) for q in (1.0, 1.0, 0.98)) + (255,)
        b = self.far
        corners = [(-ht, -ht), (ht, -ht), (ht, ht), (-ht, ht)]
        b.P += [(e + c * x - s_ * z, yc, -n + s_ * x + c * z) for x, z in corners]
        b.N += [(0.0, 1.0, 0.0)] * 4
        b.C += [tint] * 4
        b.UV += [(u0, 0.5), (u1, 0.5), (u1, 1.0), (u0, 1.0)]
        k0 = b.n
        b.F += [(k0, k0 + 2, k0 + 1), (k0, k0 + 3, k0 + 2)]          # facing up
        b.n += 4

    def _limb(self, a, b, r0, r1, col, sides):
        d = b - a
        L = np.linalg.norm(d)
        if L < 1e-3:
            return
        w = d / L
        u = np.cross(w, [0, 0, 1.0]) if abs(w[2]) < 0.9 else np.cross(w, [1.0, 0, 0])
        u /= np.linalg.norm(u)
        v = np.cross(w, u)
        for i in range(sides):
            t0, t1 = 2 * math.pi * i / sides, 2 * math.pi * (i + 1) / sides
            o0 = u * math.cos(t0) + v * math.sin(t0)
            o1 = u * math.cos(t1) + v * math.sin(t1)
            n = tuple((o0 + o1) / np.linalg.norm(o0 + o1))
            self.bark.quad(tuple(a + o0 * r0), tuple(a + o1 * r0), tuple(b + o1 * r1), tuple(b + o0 * r1), n, col)

    def _clump(self, c, s, col, rng, crown_c=None):
        """Two crossed leaf cards (one upright, one tipped over) showing a spray from the leaf atlas. Each
        card is laid twice, front and back, both with the same normal (out from the crown's middle and up),
        so the crown shades as one mass from every side (a double-sided material would turn the back
        face's normal into the crown and draw it black)."""
        cc = crown_c if crown_c is not None else c
        yaw = rng.uniform(0, math.pi)
        f = rng.uniform(0.86, 1.0)
        tint = tuple(int(255 * f * k) for k in (1.0, 1.0, 0.97)) + (255,)
        for kind in range(2):
            a = yaw + kind * math.pi / 2
            right = np.array([math.cos(a), 0.0, math.sin(a)])
            up = np.array([0.0, 1.0, 0.0])
            if kind == 1:
                f = np.cross(right, up)
                up = up * 0.45 + f * 0.89
            cell = int(rng.integers(4))
            u0, v0 = (cell % 2) * 0.5, (cell // 2) * 0.5
            r, uu = right * s, up * s
            q = [c - r - uu, c + r - uu, c + r + uu, c - r + uu]
            uv = [(u0, v0 + 0.5), (u0 + 0.5, v0 + 0.5), (u0 + 0.5, v0), (u0, v0)]
            ns = []
            for x in q:
                # out from the crown's middle, leaning well up: a gum's leaves hang edge-on and pass light,
                # so even the crown's shaded side reads grey-green from the ground, never black
                v = x - cc + np.array([0, s * 0.6, 0])
                v = 0.45 * v / (np.linalg.norm(v) + 1e-9) + np.array([0.0, 0.9, 0.0])
                ns.append(tuple(v / np.linalg.norm(v)))
            b = self.leaf
            b.P += [tuple(x) for x in q]
            b.N += ns
            b.C += [tint] * 4
            b.UV += uv
            k0 = b.n
            b.F += [(k0, k0 + 1, k0 + 2), (k0, k0 + 2, k0 + 3), (k0, k0 + 2, k0 + 1), (k0, k0 + 3, k0 + 2)]
            b.n += 4
