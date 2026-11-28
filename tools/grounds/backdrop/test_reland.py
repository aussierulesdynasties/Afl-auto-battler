"""Checks of reland.py's helpers and horizon.py's near water sheet on small made-up meshes (no ground files needed).

    python3 tools/grounds/backdrop/test_reland.py

Not run by CI (it needs numpy, scipy, shapely, rasterio and mapbox_earcut, which the lint job does not install): run it
after changing reland.py or horizon.near_water.
"""
import json
import os
import struct
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reland  # noqa: E402


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        check.failed = True


check.failed = False


def test_mesh_surface():
    # a 10 m square of two triangles, a slope from y 0 (x 0) to y 10 (x 10); its diagonal is not where a
    # re-triangulation of its corners would put it, so the sampler must use its own triangles
    P = np.array([[0, 0, 0], [10, 10, 0], [10, 10, 10], [0, 0, 10]], float)
    I = np.array([[0, 1, 2], [0, 2, 3]])
    at = reland.mesh_surface(P, I, step=1.0)
    y, t = at([5.0, 2.5, 9.99, 0.0, 20.0], [5.0, 7.5, 0.01, 0.0, 5.0])
    check(np.allclose(y[:4], [5.0, 2.5, 9.99, 0.0], atol=1e-6), "mesh_surface: heights on the mesh's own triangles")
    check(np.isnan(y[4]) and t[4] == -1, "mesh_surface: off the mesh is nan")
    # a point on a cell's edge whose cell holds the other triangle still finds its own
    y, t = at([4.0001], [3.9999])
    check(abs(y[0] - 4.0001) < 1e-4, "mesh_surface: a point by the diagonal")


def _glb(path):
    """A glb of one triangle, an unused accessor pointing past the last buffer view, and an image nothing uses."""
    pos = np.array([[0, 0, 0], [1, 0, 0], [0, 0, 1]], "<f4").tobytes()
    idx = np.array([0, 1, 2], "<u2").tobytes() + b"\0\0"
    junk = b"x" * 64
    J = {"asset": {"version": "2.0"}, "scenes": [{"nodes": [0]}], "nodes": [{"name": "bg_roads_s00", "mesh": 0}],
         "meshes": [{"name": "bg_roads_s00", "primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3"},
                       {"bufferView": 2, "componentType": 5123, "count": 3, "type": "SCALAR"},
                       {"bufferView": 9, "componentType": 5126, "count": 3, "type": "VEC3"}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(pos)},
                         {"buffer": 0, "byteOffset": len(pos), "byteLength": len(junk)},
                         {"buffer": 0, "byteOffset": len(pos) + len(junk), "byteLength": 6}],
         "buffers": [{"byteLength": len(pos) + len(junk) + len(idx)}]}
    body = pos + junk + idx
    js = json.dumps(J).encode()
    js += b" " * (-len(js) % 4)
    open(path, "wb").write(struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(body))
                           + struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(body), 0x004E4942) + body)


def test_compact():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.glb")
        _glb(p)
        g = reland.Glb(p)
        g.save()
        g2 = reland.Glb(p)
        check(len(g2.J["accessors"]) == 2 and len(g2.J["bufferViews"]) == 2, "compact: unused accessor and view dropped")
        check(np.allclose(g2.read(g2.prims[0][1]), [[0, 0, 0], [1, 0, 0], [0, 0, 1]]), "compact: positions kept")
        check(list(g2.read(g2.prims[0][2])) == [0, 1, 2], "compact: indices kept")
        n = len(g2.bin)
        g2.save()
        check(len(reland.Glb(p).bin) == n, "compact: a second save changes nothing")


def test_surrounds_outer():
    outer, reach, drop = reland.surrounds_outer("marvel")
    check(outer == 1024.0 and reach > 0 and drop > 0, "surrounds_outer: Marvel's ring ends at 1,024 m, a skirt past it")


def _write_glb(path, meshes, image=None):
    """A glb of the given meshes: [{"name", "P" (n,3), "I" (m,3), "UV" (n,2) or None}]. With image (PNG bytes), each
    mesh with UVs gets one material carrying it as base colour."""
    J = {"asset": {"version": "2.0"}, "scenes": [{"nodes": list(range(len(meshes)))}], "nodes": [], "meshes": [],
         "accessors": [], "bufferViews": [], "buffers": []}
    body = bytearray()

    def view(b):
        while len(body) % 4:
            body.append(0)
        J["bufferViews"].append({"buffer": 0, "byteOffset": len(body), "byteLength": len(b)})
        body.extend(b)
        return len(J["bufferViews"]) - 1

    def acc(arr, comp, kind):
        J["accessors"].append({"bufferView": view(arr.tobytes()), "componentType": comp, "count": len(arr), "type": kind})
        return len(J["accessors"]) - 1

    if image is not None:
        J["images"] = [{"bufferView": view(image), "mimeType": "image/png"}]
        J["textures"] = [{"source": 0}]
        J["materials"] = [{"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}]
    for k, m in enumerate(meshes):
        attrs = {"POSITION": acc(np.asarray(m["P"], "<f4"), 5126, "VEC3")}
        if m.get("UV") is not None:
            attrs["TEXCOORD_0"] = acc(np.asarray(m["UV"], "<f4"), 5126, "VEC2")
        pr = {"attributes": attrs, "indices": acc(np.asarray(m["I"], "<u4").ravel(), 5125, "SCALAR")}
        if m.get("UV") is not None and image is not None:
            pr["material"] = 0
        J["meshes"].append({"name": m["name"], "primitives": [pr]})
        J["nodes"].append({"name": m["name"], "mesh": k})
    J["buffers"] = [{"byteLength": len(body)}]
    js = json.dumps(J).encode()
    js += b" " * (-len(js) % 4)
    while len(body) % 4:
        body.append(0)
    open(path, "wb").write(struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(body))
                           + struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(body), 0x004E4942)
                           + bytes(body))


def test_lay_overlays():
    # the near ground: a 20 m square sloping up 1 m in 10 m along x (two triangles), and beside it a flat wet square at
    # the water level -2 (two triangles)
    G = np.array([[0, 0, 0], [20, 2, 0], [20, 2, 20], [0, 0, 20],
                  [-20, -2, 0], [0, -2, 0], [0, -2, 20], [-20, -2, 20]], float)
    GI = np.array([[0, 1, 2], [0, 2, 3], [4, 5, 6], [4, 6, 7]])
    # a road strip on the slope, drawn 0.6 m under it; a road triangle wholly over the wet square; a road vertex 5 m
    # up (a deck); a rail line on the slope 3 m under it (the old scene's pits)
    road = np.array([[5, -0.1, 5], [15, 0.9, 5], [15, 0.9, 6], [5, -0.1, 6],
                     [-15, -2, 5], [-5, -2, 5], [-10, -2, 10],
                     [10, 6.0, 15], [12, 6.2, 15], [11, 6.1, 16]], float)
    RI = np.array([[0, 1, 2], [0, 2, 3], [4, 5, 6], [7, 8, 9]])
    rail = np.array([[2, -2.8, 10], [18, -1.2, 10], [18, -1.2, 10.3]], float)
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.glb")
        _write_glb(p, [{"name": "bg_near_ground", "P": G, "I": GI}, {"name": "bg_roads_s00", "P": road, "I": RI},
                       {"name": "bg_rails_s00", "P": rail, "I": np.array([[0, 1, 2]])}])
        g = reland.Glb(p)
        out = reland.lay_overlays([g], -2.0)
        R = g.read(g.prims[1][1]).astype(float)
        lift = dict(reland.OVERLAY_LIFT)
        want = np.r_[G[0, 1] + R[:4, 0] * 0.1] + lift["roads"]
        check(np.allclose(R[:4, 1], want, atol=1e-4), "lay_overlays: a road on a slope sits its lift over the ground")
        check(np.allclose(R[7:, 1], [6.0, 6.2, 6.1], atol=1e-5), "lay_overlays: a deck more than 2.5 m up is left alone")
        F = g.read(g.prims[1][2]).reshape(-1, 3)
        check(len(set(F[2])) == 1, "lay_overlays: a road triangle wholly on the water is drawn as nothing")
        check(len(set(F[0])) == 3 and len(set(F[3])) == 3, "lay_overlays: other road triangles kept")
        check(out["bg_roads_s00"][2] == 1, "lay_overlays: one triangle counted as gone")
        L = g.read(g.prims[2][1]).astype(float)
        check(np.allclose(L[:, 1], L[:, 0] * 0.1 + lift["rails"], atol=1e-4), "lay_overlays: a sunken rail is raised onto the ground")
        G2 = g.read(g.prims[0][1]).astype(float)
        check(np.allclose(G2, G), "lay_overlays: the ground itself does not move")


def test_near_water():
    """horizon.near_water on Marvel's ring (outer 1,024 m + 4 m skirt): a painted harbour from 1,010 m to 1,080 m east
    of the centre. The sheet must start on the circle (none inside it), and its inner edge dive under the ring."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "horizon"))
        import horizon
    except ImportError as e:
        check(False, "near_water: horizon.py imports (%s)" % e)
        return
    import io
    from PIL import Image
    outer, reach, _ = reland.surrounds_outer("marvel")
    cx, cz = reland.fit("marvel")[:2]
    near_from = outer + reach
    img = np.zeros((8, 8, 3), np.uint8)
    img[:] = (40, 70, 95)   # the painted harbour blue (reland._water_texels)
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, "PNG")
    x0, x1, z0, z1 = 1010.0, 1080.0, -30.0, 30.0
    P = np.array([[x0, -2, z0], [x1, -2, z0], [x1, -2, z1], [x0, -2, z1]], float)
    UV = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], float)
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.glb")
        _write_glb(p, [{"name": "bg_near_ground", "P": P, "I": np.array([[0, 1, 2], [0, 2, 3]]), "UV": UV}], buf.getvalue())
        s = horizon.near_water(reland.Glb(p), -2.0, "marvel")
    check(s is not None, "near_water: a sheet is built over painted water past the ring")
    if s is None:
        return
    V = s["pos"].astype(float)
    F = s["idx"].reshape(-1, 3)
    r = np.hypot(V[:, 0] - cx, V[:, 2] - cz)
    top = V[:, 1] > -2.0
    check(r[top].min() >= near_from - 0.3, "near_water: the sheet starts on the circle, none of it inside")
    check(np.abs(r[top] - near_from).min() < 0.3, "near_water: the sheet reaches the circle")
    check(V[top, 0].max() <= x1 + 1.5 and np.abs(V[top, 2]).max() <= z1 + 1.5, "near_water: the sheet stays on the painted water")
    low = ~top
    dive_y = -2.0 - horizon.NEAR_WATER_DIVE[1] - horizon.drop(V[low, 0], V[low, 2])
    check(low.sum() > 0 and np.allclose(V[low, 1], dive_y, atol=1e-3), "near_water: the inner edge dives under the ring's water")
    check(low.any() and np.allclose(r[low], near_from - horizon.NEAR_WATER_DIVE[0], atol=0.4), "near_water: the dive reaches inside the circle")
    # the band runs the whole inner edge: the edge's points on the circle span the harbour's width
    edge = top & (r < near_from + 0.3)
    check(edge.any() and np.ptp(V[edge, 2]) > (z1 - z0) - 3, "near_water: the dive runs the whole inner edge, not only some steps")
    nrm = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])[:, 1]
    check((nrm >= 0).all(), "near_water: every triangle faces up")


if __name__ == "__main__":
    test_mesh_surface()
    test_compact()
    test_surrounds_outer()
    test_lay_overlays()
    test_near_water()
    sys.exit(1 if check.failed else 0)
