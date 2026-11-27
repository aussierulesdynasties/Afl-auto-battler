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
    # tier1 rows sit at 5.4..12.1 m, tier2 12.4..15.9 m, tier3 from 20.9 m up (parts2.py tier(), measured 2026-11-23).
    return "lo" if z < 12.25 else ("mid" if z < 18.5 else "up")


# MARVEL in red and white seats on the east wing's lower tier. Placed by a camera solved from the centre
# square in the "Marvel Stadium during curtain raiser" photo (Wikimedia Commons), its rays cast onto this
# model's tier: M's left edge at u -44.4 (north, re-checked at -40 to -43 after the tiers were lowered on
# 2026-11-23), L's right edge at u 36.5. Rows: the photo shows the letters filling the lower tier from the
# front rows up to the middle tier's overhang, which from that seat hides the lower tier above about 3.3 m. The 2026 Ed Sheeran stage photo (NAB House behind that stand) puts it on the east wing. White
# block capitals on a red block, read from the west stand.
U_AX = np.array([0.33632, -0.94215]); V_AX = np.array([-0.94215, -0.33632]); FIELD_Z = 5.4
LET_U = (-44.4, 36.5); LET_Z = (FIELD_Z + 0.3, FIELD_Z + 3.4)


def _letter_mask():
    """MARVEL in the venue's own letters (fonts/marvel_stadium_logo.png, as retint.sign_panels), not a stock font
    (round 17: the person's audit; the modelling rules ban stock fonts)."""
    from PIL import Image
    w, h = 324, 20  # 0.25 m across, 0.23 m up
    logo = np.asarray(Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts",
                                              "marvel_stadium_logo.png")).convert("RGBA"), float)
    rgb, al = logo[..., :3], logo[..., 3] / 255.0
    mv = ((al > 0.5) & (rgb.min(2) > 200))[36:379, 484:1437]
    im = Image.fromarray((mv * 255).astype(np.uint8)).resize((w - 8, h - 4), Image.LANCZOS)
    out = Image.new("L", (w, h), 0); out.paste(im, (4, 2))
    return np.array(out) > 110


def lettering(S: np.ndarray, C: np.ndarray) -> np.ndarray:
    """0 = not in the block, 1 = red, 2 = white, per seat."""
    m = _letter_mask(); h, w = m.shape
    d = S[:, :2] - C[:2]; u = d @ U_AX; v = d @ V_AX; z = S[:, 2]
    inb = (v < -40) & (u >= LET_U[0]) & (u <= LET_U[1]) & (z >= LET_Z[0]) & (z <= LET_Z[1])
    col = np.clip(((u - LET_U[0]) / (LET_U[1] - LET_U[0]) * w).astype(int), 0, w - 1)
    row = np.clip(((LET_Z[1] - z) / (LET_Z[1] - LET_Z[0]) * h).astype(int), 0, h - 1)
    res = np.zeros(len(S), int); res[inb] = 1
    res[inb & m[row, col]] = 2
    return res


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
    let = lettering(S, C0)
    for i in range(len(S)):
        groups.setdefault(("mred", "mwhite")[let[i] - 1] if let[i] else tier_of(S[i, 2]), []).append(i)
    for t, idx in sorted(groups.items()):
        idx = np.array(idx)
        X, Y, Z, O = side[idx], np.tile(up, (len(idx), 1)), zaxis[idx], pos[idx]
        # row-major 3x4: [Xx Yx Zx Ox, Xy Yy Zy Oy, Xz Yz Zz Oz]
        M = np.stack([X[:, 0], Y[:, 0], Z[:, 0], O[:, 0], X[:, 1], Y[:, 1], Z[:, 1], O[:, 1], X[:, 2], Y[:, 2], Z[:, 2], O[:, 2]], 1)
        M.astype(np.float32).tofile(os.path.join(OUT, "seats_seat_marvel_%s.bin" % t))
        print(t, len(idx), "seats, y %.1f..%.1f" % (O[:, 1].min(), O[:, 1].max()))


if __name__ == "__main__":
    main()
