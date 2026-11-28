"""Checks of reland.py's helpers on small made-up meshes (no ground files needed).

    python3 tools/grounds/backdrop/test_reland.py

Not run by CI (it needs numpy and scipy, which the lint job does not install): run it after changing reland.py.
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


if __name__ == "__main__":
    test_mesh_surface()
    test_compact()
    test_surrounds_outer()
    sys.exit(1 if check.failed else 0)
