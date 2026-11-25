"""Our stands against Google Earth's, in metres: python3 compare_stand.py [plot.png]

stand_probe.json (probe.py read_stand) holds, for spots along 60 bearings, the true east/north and the height above
the turf of what Google Earth shows there. Here our model (assets/grounds/york_park/york_park.glb) is sampled
straight down at the same spots, and per bearing the two profiles are compared: where the roof's front edge
and back edge fall (the first and last spot over 6 m), and the roof height. A plot shows each bearing's profile.
"""
import json, math, os, sys
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(HERE, "..", "..", "..", "..", "assets", "grounds", "york_park", "york_park.glb")


def ours(points):
    sc = trimesh.load(GLB, force="scene")
    mesh = sc.to_geometry()                       # glTF frame: x east, y up, z south
    ray = trimesh.ray.ray_triangle.RayMeshIntersector(mesh)
    o = np.array([[e, 200.0, -n] for e, n in points]); d = np.tile([0, -1.0, 0], (len(o), 1))
    loc, idx, _ = ray.intersects_location(o, d, multiple_hits=False)
    h = np.full(len(o), 0.0)
    h[idx] = loc[:, 1]
    return h


def edges(rs, hs, th=6.0):
    up = [r for r, h in zip(rs, hs) if h > th]
    return (min(up), max(up)) if up else (None, None)


def main(plot=None):
    P = json.load(open(os.path.join(HERE, "stand_probe.json")))
    pts = [(e, n) for _, _, e, n, _ in P]
    oh = ours(pts)
    by = {}
    for (b, r, e, n, h), o in zip(P, oh):
        rr = math.hypot(e, n)
        by.setdefault(b, []).append((rr, h, o))
    rows = []
    print("bearing  GE roof front-back (m)   ours front-back   GE top  ours top")
    for b in sorted(by):
        v = sorted(by[b])
        rs = [x[0] for x in v]
        g0, g1 = edges(rs, [x[1] for x in v]); o0, o1 = edges(rs, [x[2] for x in v])
        gt = max(x[1] for x in v); ot = max(x[2] for x in v)
        rows.append((b, g0, g1, o0, o1, gt, ot))
        f = lambda x: "  --  " if x is None else "%6.1f" % x
        print("%5d     %s %s        %s %s     %5.1f  %5.1f" % (b, f(g0), f(g1), f(o0), f(o1), gt, ot))
    json.dump(rows, open(os.path.join(HERE, "stand_compare.json"), "w"))
    if plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        bs = sorted(by)
        n = len(bs); cols = 6; fig, ax = plt.subplots((n + cols - 1) // cols, cols, figsize=(cols * 3.2, ((n + cols - 1) // cols) * 2.2))
        for a, b in zip(ax.ravel(), bs):
            v = sorted(by[b])
            a.plot([x[0] for x in v], [x[1] for x in v], "-", color="#2a6", lw=1.5, label="Google Earth")
            a.plot([x[0] for x in v], [x[2] for x in v], "-", color="#c33", lw=1.2, label="ours")
            a.set_title("bearing %d" % b, fontsize=8); a.set_ylim(-1, 30); a.tick_params(labelsize=6)
        ax.ravel()[0].legend(fontsize=6)
        for a in ax.ravel()[n:]:
            a.axis("off")
        fig.tight_layout(); fig.savefig(plot, dpi=90)
        print("plot", plot)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
