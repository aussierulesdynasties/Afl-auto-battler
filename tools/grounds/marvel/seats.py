"""Marvel Stadium's seats as instanced seats (GroundModels: seat_tmpl.bin + seats_<colour>.bin).

The model (.claude/review/marvel/mv2) baked 57,535 seats into two meshes of a million triangles each.
Every other ground draws one seat many times, which the phone can cull slice by slice and the crowd
can sit on. This reads the same seat spots (parts2.json `seats`: x, y, z on the tread, the way to the
pitch) and writes them in the game model's own frame (glTF: x east, y up, -z north), one file per tier
so each tier keeps its own colour. Looks only.

    python3 tools/grounds/marvel/seats.py            # writes assets/grounds/marvel/seat_tmpl.bin, seats_seat_marvel_*.bin
"""
import json, math, os, sys
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, ".claude", "review", "marvel", "mv2", "parts2.json")
OUT = os.path.join(ROOT, "assets", "grounds", "marvel")

J = json.load(open(SRC))
C0 = np.array(J.get("C", [2.32, 0.64, 0.0]))
ANG = 0.0  # build2.py glb exports the frame as it is: x east, y north

# The seat as build2.py drew it (x along the row, y towards the pitch, z up; origin on the tread):
# pan, back and pedestal, 0.44 m wide.
def _bx(x0, x1, y0, y1, z0, z1):
    return [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
_BF = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
BOXES = [_bx(-0.22, 0.22, -0.22, 0.20, 0.40, 0.46), _bx(-0.22, 0.22, -0.30, -0.24, 0.46, 0.86), _bx(-0.025, 0.025, -0.12, -0.04, 0.0, 0.40)]


def template() -> np.ndarray:
    """Triangles in the seat's glTF space: X along the row, Y up, Z away from the pitch."""
    tris = []
    for b in BOXES:
        for f in _BF:
            q = [b[i] for i in f]
            for t in ((q[0], q[1], q[2]), (q[0], q[2], q[3])):
                # Blender (x, y, z) -> glTF (x, z, -y); y towards the pitch = -Z. Winding kept CCW from outside.
                tris += [(p[0], p[2], -p[1]) for p in t]
    return np.array(tris, np.float32)


def to_gltf(p: np.ndarray) -> np.ndarray:
    """Blender world (after - C0), rotated by ANG about Z, then to glTF axes."""
    c, s = math.cos(ANG), math.sin(ANG)
    x = c * p[:, 0] - s * p[:, 1]
    y = s * p[:, 0] + c * p[:, 1]
    return np.stack([x, p[:, 2], -y], 1)


def tier_of(z: float) -> str:
    # tier1 rows sit at 5.4..16 m, tier2 19..27 m, tier3 30.5 m up (parts2.py tier()).
    return "lo" if z < 17.5 else ("mid" if z < 28.5 else "up")


def main() -> None:
    S = np.array(J["seats"], float)
    pos = to_gltf(S[:, :3] - C0)
    fwd = to_gltf(np.c_[S[:, 3:5], np.zeros(len(S))])
    fwd /= np.linalg.norm(fwd, axis=1, keepdims=True)
    up = np.array([0.0, 1.0, 0.0])
    side = np.cross(fwd, up)  # build2: side = (fwd.y, -fwd.x) in Blender, i.e. fwd x up
    zaxis = -fwd  # seat Z points away from the pitch
    tmpl = template()
    # Check the side axis matches build2.py's: Blender side=(fy,-fx,0) -> glTF (fy, 0, fx).
    os.makedirs(OUT, exist_ok=True)
    tmpl.tofile(os.path.join(OUT, "seat_tmpl.bin"))
    groups = {}
    for i in range(len(S)):
        groups.setdefault(tier_of(S[i, 2]), []).append(i)
    for t, idx in sorted(groups.items()):
        idx = np.array(idx)
        X, Y, Z, O = side[idx], np.tile(up, (len(idx), 1)), zaxis[idx], pos[idx]
        # row-major 3x4: [Xx Yx Zx Ox, Xy Yy Zy Oy, Xz Yz Zz Oz]
        M = np.stack([X[:, 0], Y[:, 0], Z[:, 0], O[:, 0], X[:, 1], Y[:, 1], Z[:, 1], O[:, 1], X[:, 2], Y[:, 2], Z[:, 2], O[:, 2]], 1)
        M.astype(np.float32).tofile(os.path.join(OUT, "seats_seat_marvel_%s.bin" % t))
        print(t, len(idx), "seats, y %.1f..%.1f" % (O[:, 1].min(), O[:, 1].max()))


if __name__ == "__main__":
    main()
