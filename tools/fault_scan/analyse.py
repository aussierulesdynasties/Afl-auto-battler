"""The fault scan's measuring half (tools/fault_scan/README.md). Reads scan.gd's dump of one ground (world
space, the ground inspector's coordinates) and OpenStreetMap round it (osm.py), runs every geometric check,
and writes findings.json and the camera list for the renders (views.txt).

    python3 tools/fault_scan/analyse.py <dump_dir> <out_dir>

Needs numpy, scipy, trimesh, embreex, shapely, pillow.
"""
import json, math, os, sys, time
from collections import Counter, defaultdict

import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
import trimesh
from trimesh.ray.ray_pyembree import RayMeshIntersector

T0 = time.time()
INF = float("inf")


def log(*a):
    print("[%6.1f s]" % (time.time() - T0), *a, flush=True)


# --- loading ---------------------------------------------------------------------------------------

SURROUND_TOP = ("surrounds", "buildings", "trees", "trunks", "treesfar", "gums", "land", "towers", "apronskirt",
                "relief", "park")
LAND_WORDS = ("terrain", "ground", "grass", "land", "park", "water", "road", "street", "footpath", "kerb",
              "pavement", "plaza", "asphalt", "parking", "carpark", "car_park", "lawn", "concourse", "path",
              "surrounds", "turf", "forecourt", "rail", "tram", "sea", "river", "bay", "dirt", "sand", "paving")
ROAD_WORDS = ("road", "street", "asphalt", "lane", "highway", "tram", "carriageway", "bitumen")
TREE_WORDS = ("tree", "leaf", "leaves", "canopy", "foliage", "gum", "palm", "crown", "bark", "trunk", "hedge", "bush")
SIGN_WORDS = ("sign", "logo", "board", "banner", "text", "letter", "name", "screen", "advert", "ad_", "brand",
              "scoreboard", "display", "poster", "wordmark", "lcd", "led", "signage", "billboard")


def top_name(node):
    p = node.split("/")
    return p[1] if len(p) > 1 and p[0] == "Ground" else p[0]


def category(node):
    if not node.startswith("Ground"):
        return "oval"
    t = top_name(node).lower()
    if t == "backdrop":
        return "backdrop"
    if t.startswith(SURROUND_TOP) or t.startswith("seats_") or t.startswith("legs_"):
        return "surrounds"
    return "model"


class Dump:
    def __init__(self, d):
        self.d = d
        self.g = json.load(open(os.path.join(d, "ground.json")))
        self.surf = json.load(open(os.path.join(d, "surfaces.json")))
        self.mms = json.load(open(os.path.join(d, "multimesh.json")))
        self.tex = json.load(open(os.path.join(d, "textures.json")))
        V = np.fromfile(os.path.join(d, "verts.f32"), dtype=np.float32).reshape(-1, 3)
        N = np.fromfile(os.path.join(d, "nrms.f32"), dtype=np.float32).reshape(-1, 3)
        UV = np.fromfile(os.path.join(d, "uvs.f32"), dtype=np.float32).reshape(-1, 2)
        I = np.fromfile(os.path.join(d, "idx.i32"), dtype=np.int32)
        tris, sid = [], []
        for k, s in enumerate(self.surf):
            ix = I[s["istart"]:s["istart"] + s["icount"]].astype(np.int64) + s["vstart"]
            ix = ix[: len(ix) // 3 * 3].reshape(-1, 3)
            tris.append(ix)
            sid.append(np.full(len(ix), k, dtype=np.int32))
            s["cat"] = category(s["node"])
            # the node path less its "Ground/" root (every path has it), the mesh and the material
            path = s["node"].split("/", 1)[1] if s["node"].startswith("Ground/") else s["node"]
            s["name"] = (path + " " + s["mesh"] + " " + str(s["material"].get("name", ""))).lower()
        self.V, self.N, self.UV = V.astype(np.float64), N.astype(np.float64), UV.astype(np.float64)
        self.F = np.concatenate(tris) if tris else np.zeros((0, 3), np.int64)
        self.sid = np.concatenate(sid) if sid else np.zeros(0, np.int32)
        self.cat = np.array([s["cat"] for s in self.surf])[self.sid] if len(self.sid) else np.array([])
        log("loaded %d surfaces, %d vertices, %d triangles, %d multimeshes" % (
            len(self.surf), len(V), len(self.F), len(self.mms)))

    def mm(self, m):
        buf = np.fromfile(os.path.join(self.d, m["file"]), dtype=np.float32)
        stride = 12 + (4 if m["colors"] else 0) + (4 if m["custom"] else 0)
        buf = buf[: len(buf) // stride * stride].reshape(-1, stride)
        x = np.array(m["xform"], dtype=np.float64).reshape(3, 4)
        G = np.eye(4)
        G[:3, :] = x
        L = np.zeros((len(buf), 4, 4))
        L[:, :3, :] = buf[:, :12].reshape(-1, 3, 4)
        L[:, 3, 3] = 1.0
        W = G[None] @ L
        faces = np.fromfile(os.path.join(self.d, m["file"].replace(".f32", "_faces.f32")),
                            dtype=np.float32).reshape(-1, 3).astype(np.float64)
        return W, faces


# --- frames ----------------------------------------------------------------------------------------

def enu_to_world(e, n, axis, mirror=False):
    a = math.radians(axis)
    x = e * math.sin(a) + n * math.cos(a)
    z = e * math.cos(a) - n * math.sin(a)
    return (x, -z) if mirror else (x, z)


def view_line(name, eye, target, fov=60.0):
    d = np.asarray(target, float) - np.asarray(eye, float)
    d = d / (np.linalg.norm(d) + 1e-9)
    yaw = math.atan2(-d[0], -d[2])
    facing = (math.degrees(-yaw)) % 360.0
    looking = math.degrees(math.asin(max(-1.0, min(1.0, d[1]))))
    return "%s %.2f %.2f %.2f %.2f %.2f %.1f" % (name, eye[0], eye[1], eye[2], facing, looking, fov)


def where(p, facing=None, looking=None):
    s = "x %.1f  y %.1f  z %.1f" % (p[0], p[1], p[2])
    if facing is not None:
        s += ", facing %d deg, looking %+d deg" % (round(facing) % 360, round(looking))
    return s


def view_where(line):
    w = line.split()
    return "x %s  y %s  z %s, facing %d deg, looking %+d deg" % (
        "%.1f" % float(w[1]), "%.1f" % float(w[2]), "%.1f" % float(w[3]), round(float(w[4])) % 360, round(float(w[5])))


# --- the scan --------------------------------------------------------------------------------------

class Scan:
    def __init__(self, dump, osm, out="."):
        self.out = out
        self.D = dump
        self.osm = osm
        self.findings = []
        self.views = []
        self.stats = {}
        D = dump
        self.tri = D.V[D.F] if len(D.F) else np.zeros((0, 3, 3))
        c = self.tri.mean(axis=1)
        self.cen = c
        rh = np.hypot(c[:, 0], c[:, 2])
        # The scene the rays see: everything within 1.6 km (the far hills only slow the rays down).
        keep = rh < 1600.0
        self.keep_idx = np.nonzero(keep)[0]
        legs_tris, self.leg_info = self._instances_tris(lambda n: n.startswith("legs_"))
        tri = np.concatenate([self.tri[keep], legs_tris]) if len(legs_tris) else self.tri[keep]
        self.n_mesh = int(keep.sum())
        verts = tri.reshape(-1, 3)
        faces = np.arange(len(verts)).reshape(-1, 3)
        self.mesh = trimesh.Trimesh(verts, faces, process=False)
        self.ray = RayMeshIntersector(self.mesh)
        log("ray scene: %d triangles (%d legs)" % (len(faces), len(legs_tris)))
        self.fx, self.fz = D.g["fence"]

    # the source triangle of a ray-scene face: >= 0 a mesh triangle, < 0 a leg instance
    def src(self, face):
        face = np.asarray(face)
        out = np.full(face.shape, -1, dtype=np.int64)
        ok = (face >= 0) & (face < self.n_mesh)
        out[ok] = self.keep_idx[face[ok]]
        return out

    def first(self, o, d):
        o = np.asarray(o, float).reshape(-1, 3)
        d = np.asarray(d, float).reshape(-1, 3)
        d = d / np.linalg.norm(d, axis=1, keepdims=True)
        if len(o) == 0:
            return np.zeros(0, int), np.zeros((0, 3)), np.zeros(0)
        idx = self.ray.intersects_first(o, d)
        loc = np.full((len(o), 3), np.nan)
        dist = np.full(len(o), INF)
        hit = idx >= 0
        if hit.any():
            t = self.mesh.triangles[idx[hit]]
            # exact point on the plane of the hit triangle
            nrm = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
            denom = np.einsum("ij,ij->i", nrm, d[hit])
            denom[np.abs(denom) < 1e-12] = 1e-12
            s = np.einsum("ij,ij->i", nrm, t[:, 0] - o[hit]) / denom
            loc[hit] = o[hit] + d[hit] * s[:, None]
            dist[hit] = s
        return idx, loc, dist

    def _instances_tris(self, pick):
        out, info = [], []
        for m in self.D.mms:
            nm = m["node"].split("/")[-1]
            if not pick(nm):
                continue
            W, faces = self.D.mm(m)
            if len(W) == 0 or len(faces) == 0:
                continue
            fh = np.c_[faces, np.ones(len(faces))]
            pts = np.einsum("nij,kj->nki", W[:, :3, :], fh)
            out.append(pts.reshape(-1, 3, 3))
            info.append((m, W, faces))
        if not out:
            return np.zeros((0, 3, 3)), info
        return np.concatenate(out), info

    def add(self, check, title, where_p, detail, cause, severity="fault", view=None, extra=None, more_views=()):
        f = {"id": len(self.findings) + 1, "check": check, "title": title, "where": [round(float(v), 1) for v in where_p],
             "detail": detail, "cause": cause, "severity": severity}
        vs = ([view] if view is not None else []) + list(more_views)
        f["views"] = []
        for k, v in enumerate(vs[:4]):
            vname = "f%03d_%s%s" % (f["id"], check, "" if k == 0 else "_%d" % k)
            self.views.append(view_line(vname, v[0], v[1], v[2] if len(v) > 2 else 55.0))
            f["views"].append({"name": vname, "where": view_where(self.views[-1]), "target": [round(float(t), 1) for t in v[1]]})
        if extra:
            f.update(extra)
        self.findings.append(f)
        return f

    def close_view(self, p, n=None, dist=12.0, fov=55.0):
        """A camera dist m off point p, along the face normal n when given, else from the field side."""
        p = np.asarray(p, float)
        if n is None or not np.isfinite(n).all() or np.linalg.norm(n) < 1e-6:
            h = np.array([-p[0], 0.0, -p[2]])
            n = h / (np.linalg.norm(h) + 1e-9) + np.array([0, 0.35, 0])
        n = np.asarray(n, float) / (np.linalg.norm(n) + 1e-9)
        eye = p + n * dist
        eye[1] = max(eye[1], p[1] - dist * 0.9, 0.5)
        return (eye, p, fov)

    # ---- checks ------------------------------------------------------------------------------------

    def run(self):
        for fn in (self.check_components, self.check_textures, self.check_print, self.check_seats, self.check_legs,
                   self.check_sky, self.check_trees, self.check_frame_and_roads, self.check_osm_structures,
                   self.check_buildings, self.check_generic, self.check_inside_fence, self.make_views):
            try:
                log("check", fn.__name__)
                fn()
            except Exception as ex:  # noqa: BLE001 - one broken check must not hide the others
                import traceback
                traceback.print_exc()
                self.stats.setdefault("check_errors", []).append("%s: %s" % (fn.__name__, ex))
        log("findings: %d" % len(self.findings))

    # 1. Signs and boards: mirrored text, stretched textures, dull colours ---------------------------
    def check_textures(self):
        D = self.D
        tex_info = {k: v for k, v in D.tex.items()}
        groups = defaultdict(list)
        for k, s in enumerate(D.surf):
            m = s["material"]
            tid = m.get("tex") or ""
            if not tid and m.get("params"):
                for pn, pv in m["params"].items():
                    if isinstance(pv, str) and pv and any(w in pn.lower() for w in ("albedo", "tex", "map", "color")):
                        tid = pv
                        break
            if tid and tid in tex_info:
                groups[k] = tid
        self.stats["textured_surfaces"] = len(groups)
        mirrored, stretched, dull, backs = [], [], [], []
        for k, tid in groups.items():
            s = D.surf[k]
            sel = np.nonzero(D.sid == k)[0]
            if len(sel) == 0:
                continue
            F = D.F[sel]
            P = D.V[F]
            UVs = D.UV[F]
            scale = s["material"].get("uv1_scale", [1, 1, 1])
            UVs = UVs * np.array([scale[0], scale[1]])[None, None, :]
            e1, e2 = P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]
            d1, d2 = UVs[:, 1] - UVs[:, 0], UVs[:, 2] - UVs[:, 0]
            det = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]
            ok = np.abs(det) > 1e-10
            area = 0.5 * np.linalg.norm(np.cross(e1, e2), axis=1)
            ok &= area > 1e-4
            if ok.sum() == 0:
                continue
            r = 1.0 / det[ok]
            T = (e1[ok] * d2[ok, 1:2] - e2[ok] * d1[ok, 1:2]) * r[:, None]
            B = (e2[ok] * d1[ok, 0:1] - e1[ok] * d2[ok, 0:1]) * r[:, None]
            nv = D.N[F[ok]].mean(axis=1)
            geo = np.cross(e1[ok], e2[ok])
            # Godot's front face is clockwise seen from the front, so the face normal is -geo (det>0 frames).
            nlen = np.linalg.norm(nv, axis=1)
            nrm = np.where(nlen[:, None] > 1e-6, nv, -geo)
            hand = np.einsum("ij,ij->i", np.cross(T, B), nrm)
            a = area[ok]
            tinfo = tex_info[tid]
            W, H = max(1, tinfo["w"]), max(1, tinfo["h"])
            ratio = (np.linalg.norm(T, axis=1) / W) / np.maximum(1e-12, np.linalg.norm(B, axis=1) / H)
            uvr = UVs[ok].reshape(-1, 2)
            span = uvr.max(axis=0) - uvr.min(axis=0)
            tiling = bool(span[0] > 1.6 or span[1] > 1.6)
            tot = a.sum()
            mir = a[hand > 0].sum() / tot
            # Area-weighted median of the pixel aspect.
            o = np.argsort(np.log(ratio))
            cum = np.cumsum(a[o])
            med = float(ratio[o][np.searchsorted(cum, cum[-1] / 2)])
            c = (P[ok].mean(axis=1) * a[:, None]).sum(axis=0) / tot
            nmean = (nrm / np.maximum(1e-9, np.linalg.norm(nrm, axis=1, keepdims=True)) * a[:, None]).sum(axis=0)
            name = s["name"]
            signy = any(w in name or w in tid.lower() for w in SIGN_WORDS)
            ent = {"k": k, "tid": tid, "tex_key": tinfo["key"], "area": float(tot), "mirrored": float(mir),
                   "ratio": med, "tiling": tiling, "centre": c, "normal": nmean, "signy": signy,
                   "cull": s["material"].get("cull"), "cat": s["cat"], "node": s["node"],
                   "albedo": s["material"].get("albedo"), "mat": s["material"].get("name", "")}
            if not tiling and tot > 0.5 and mir > 0.5 and s["cat"] != "oval":
                mirrored.append(ent)
            if tot > 2.0 and (med > 1.3 or med < 1 / 1.3) and s["cat"] != "oval" and not tiling:
                stretched.append(ent)
            if not tiling and s["material"].get("cull") == 2 and tot > 0.5 and signy:
                backs.append(ent)
            alb = s["material"].get("albedo")
            if signy and alb and (0.2126 * alb[0] + 0.7152 * alb[1] + 0.0722 * alb[2]) < 0.8 and not tiling:
                dull.append(ent)
        # Merge by texture so one sign drawn as many pieces is one finding.
        def merged(lst):
            by = defaultdict(list)
            for e in lst:
                by[(e["tid"], round(e["centre"][0] / 25), round(e["centre"][2] / 25))].append(e)
            return list(by.values())

        for grp in merged(mirrored):
            e = max(grp, key=lambda x: x["area"])
            area = sum(x["area"] for x in grp)
            self.add("mirrored_text", "Texture drawn mirrored (any words on it read backwards)", e["centre"],
                     "%s on %s: %.0f%% of %.1f m2 is drawn mirror-image from its front side (texture %s, %s)." % (
                         e["mat"] or "material", e["node"], 100 * e["mirrored"], area, e["tex_key"], e["tid"].split("/")[-1]),
                     "The UVs run right-to-left as seen from the face's front: the mesh was built in the model's "
                     "mirrored frame and its UVs were not flipped back.",
                     view=self.close_view(e["centre"], e["normal"], max(6.0, math.sqrt(area) * 1.4)),
                     extra={"texture": e["tex_key"], "signy": e["signy"]})
        for grp in merged(stretched):
            e = max(grp, key=lambda x: x["area"])
            r = e["ratio"]
            how = "stretched %.0f%% wider than tall" % (100 * (r - 1)) if r > 1 else "squashed to %.0f%% of its width" % (100 * r)
            self.add("stretched_texture", "Texture stretched or squashed (wrong aspect)", e["centre"],
                     "%s on %s: each texture pixel covers %.2f times as much along the texture's width as its height (%s); texture %s." % (
                         e["mat"] or "material", e["node"], r, how, e["tex_key"]),
                     "The UVs do not match the face's real proportions (the image was fitted to a face of another shape).",
                     view=self.close_view(e["centre"], e["normal"], max(6.0, math.sqrt(e["area"]) * 1.4)),
                     extra={"texture": e["tex_key"], "signy": e["signy"]})
        for grp in merged(backs):
            e = max(grp, key=lambda x: x["area"])
            self.add("sign_back_mirrored", "Sign drawn on both sides (reads backwards from behind)", e["centre"],
                     "%s on %s is two-sided with one texture: from behind, its print shows mirror-image." % (e["mat"], e["node"]),
                     "Cull mode disabled on a printed face; the back needs its own face (blank or the reverse print).",
                     view=self.close_view(e["centre"], -np.asarray(e["normal"]), 10.0), extra={"texture": e["tex_key"]})
        for grp in merged(dull):
            e = max(grp, key=lambda x: x["area"])
            alb = e["albedo"]
            self.add("dull_sign", "Sign colours darkened by its material", e["centre"],
                     "%s on %s multiplies its texture by %.2f %.2f %.2f, so the print is dimmer than the artwork." % (
                         e["mat"], e["node"], alb[0], alb[1], alb[2]),
                     "Material albedo colour below white on a printed sign.",
                     view=self.close_view(e["centre"], e["normal"], 10.0), extra={"texture": e["tex_key"]})
        self.stats["textures_checked"] = len(groups)

    # 1b. Printed boards read from the front, as a person sees them: backwards or upside-down words ---------
    def _ocr_score(self, img):
        try:
            import pytesseract
        except ImportError:
            return 0.0, ""
        best, words = 0.0, ""
        for im in (img, img.resize((img.width * 2, img.height * 2))):
            try:
                d = pytesseract.image_to_data(im.convert("L"), config="--psm 11", output_type=pytesseract.Output.DICT)
            except Exception:  # noqa: BLE001 - no tesseract binary
                return 0.0, ""
            sc, ws = 0.0, []
            for w, c in zip(d["text"], d["conf"]):
                w = "".join(ch for ch in str(w) if ch.isalnum())
                try:
                    c = float(c)
                except ValueError:
                    continue
                if len(w) >= 3 and c > 60 and sum(ch.isalpha() for ch in w) >= 3:
                    sc += c / 100.0 * len(w)
                    ws.append(w)
            if sc > best:
                best, words = sc, " ".join(ws[:8])
        return best, words

    def check_print(self):
        from PIL import Image, ImageOps
        D = self.D
        comp_of = getattr(self, "comp_of", None)
        if comp_of is None:
            return
        os.makedirs(os.path.join(self.out, "prints"), exist_ok=True)
        by_key = {v["key"]: (k, v) for k, v in D.tex.items()}
        # which textures carry words at all (either way round)
        texty = {}
        for k, v in D.tex.items():
            fp = os.path.join(D.d, "tex", v["key"] + ".png")
            if not os.path.exists(fp):
                continue
            im = Image.open(fp).convert("RGB")
            a, wa = self._ocr_score(im)
            b, wb = self._ocr_score(ImageOps.mirror(im))
            if max(a, b) >= 4.0:
                texty[k] = (a, b, wa, wb)
        self.stats["textures_with_words"] = len(texty)
        log("textures with words: %d" % len(texty))
        groups = defaultdict(list)
        for k, sf in enumerate(D.surf):
            tid = sf["material"].get("tex") or ""
            if not tid:
                for pn, pv in (sf["material"].get("params") or {}).items():
                    if isinstance(pv, str) and pv in D.tex:
                        tid = pv
                        break
            if tid not in texty or sf["cat"] == "oval":
                continue
            sel = np.nonzero(D.sid == k)[0]
            for t, c in zip(sel, comp_of[sel]):
                groups[(k, int(c), tid)].append(t)
        cand = sorted(groups.items(), key=lambda kv: -len(kv[1]))[:400]
        n_back = 0
        for (k, c, tid), tl in cand:
            tl = np.array(tl)
            F = D.F[tl]
            P = D.V[F]
            UV = D.UV[F]
            e1, e2 = P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]
            d1, d2 = UV[:, 1] - UV[:, 0], UV[:, 2] - UV[:, 0]
            det = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]
            area = 0.5 * np.linalg.norm(np.cross(e1, e2), axis=1)
            ok = (np.abs(det) > 1e-10) & (area > 1e-5)
            if area[ok].sum() < 0.4:
                continue
            r = 1.0 / det[ok]
            T = ((e1[ok] * d2[ok, 1:2] - e2[ok] * d1[ok, 1:2]) * r[:, None] * area[ok, None]).sum(0) / area[ok].sum()
            B = ((e2[ok] * d1[ok, 0:1] - e1[ok] * d2[ok, 0:1]) * r[:, None] * area[ok, None]).sum(0) / area[ok].sum()
            nv = D.N[F[ok]].mean(axis=1)
            n = (nv * area[ok, None]).sum(0)
            if np.linalg.norm(n) < 1e-9:
                n = -np.cross(e1[ok], e2[ok]).sum(0)
            n = n / (np.linalg.norm(n) + 1e-12)
            up = np.array([0, 1.0, 0]) - n * n[1]
            if np.linalg.norm(up) < 0.3:   # lying flat: read it with the texture's own up
                up = -B - n * np.dot(-B, n)
            up /= np.linalg.norm(up) + 1e-12
            right = np.cross(up, n)
            A = np.array([[T @ right, B @ right], [T @ up, B @ up]])
            if abs(np.linalg.det(A)) < 1e-12:
                continue
            M = np.linalg.inv(A)
            pts = P[ok].reshape(-1, 3)
            uvs = UV[ok].reshape(-1, 2)
            rr, uu = pts @ right, pts @ up
            rc, uc = rr.mean(), uu.mean()
            uvc = uvs.mean(axis=0) - (M @ np.vstack([rr - rc, uu - uc])).T.mean(axis=0)
            wm, hm = rr.max() - rr.min(), uu.max() - uu.min()
            if wm < 0.3 or hm < 0.1:
                continue
            sc = 360.0 / max(wm, hm)
            wp, hp = max(8, int(wm * sc)), max(8, int(hm * sc))
            ii, jj = np.meshgrid(np.arange(wp), np.arange(hp))
            sr = rr.min() + (ii + 0.5) / wp * wm - rc
            su = uu.max() - (jj + 0.5) / hp * hm - uc
            u = uvc[0] + M[0, 0] * sr + M[0, 1] * su
            v = uvc[1] + M[1, 0] * sr + M[1, 1] * su
            key = D.tex[tid]["key"]
            src = np.asarray(Image.open(os.path.join(D.d, "tex", key + ".png")).convert("RGB"))
            th, tw = src.shape[:2]
            px = np.clip((np.mod(u, 1.0) * tw).astype(int), 0, tw - 1)
            py = np.clip((np.mod(v, 1.0) * th).astype(int), 0, th - 1)
            shown = Image.fromarray(src[py, px])
            a, wa = self._ocr_score(shown)
            b, wb = self._ocr_score(ImageOps.mirror(shown))
            c2, wc = self._ocr_score(shown.rotate(180))
            ctr = pts.mean(axis=0)
            if max(b, c2) > max(4.0, 1.5 * a):
                n_back += 1
                fn = "print_%04d.png" % n_back
                shown.save(os.path.join(self.out, "prints", fn))
                how = "backwards (mirror-image)" if b >= c2 else "upside down"
                self.add("backwards_text", "Words on a sign read %s" % how.split(" ")[0], ctr,
                         "%s on %s (texture %s): seen from its front the print reads %s. Read the right way it says "
                         "\"%s\"; as drawn it reads \"%s\". %.1f x %.1f m. The board as drawn is prints/%s." % (
                             D.surf[k]["material"].get("name", "board"), D.surf[k]["node"], key, how,
                             wb if b >= c2 else wc, wa, wm, hm, fn),
                         "The board's UVs were laid in the model's mirrored frame and not flipped back for this face.",
                         view=self.close_view(ctr, n, max(5.0, max(wm, hm) * 1.3)), extra={"print": fn, "texture": key})
        self.stats["prints_checked"] = len(cand)

    # 2. Floating objects (connected pieces touching nothing) and legs that stop short ---------------
    def check_components(self):
        D = self.D
        cat = D.cat
        near = np.nonzero(((cat == "model") | (cat == "surrounds") | (cat == "backdrop"))
                          & (np.hypot(self.cen[:, 0], self.cen[:, 2]) < 700.0))[0]
        if len(near) == 0:
            return
        F = D.F[near]
        q = np.round(D.V[F.reshape(-1)] / 0.02).astype(np.int64)
        _, vid = np.unique(q, axis=0, return_inverse=True)
        vid = vid.reshape(-1, 3)
        nv = vid.max() + 1
        rows = np.r_[vid[:, 0], vid[:, 1]]
        cols = np.r_[vid[:, 1], vid[:, 2]]
        g = sparse.coo_matrix((np.ones(len(rows), np.int8), (rows, cols)), shape=(nv, nv))
        ncomp, lab = connected_components(g, directed=False)
        tcomp = lab[vid[:, 0]]
        log("components: %d over %d triangles" % (ncomp, len(near)))
        P = D.V[F]
        lo = np.full((ncomp, 3), INF)
        hi = np.full((ncomp, 3), -INF)
        np.minimum.at(lo, tcomp, P.min(axis=1))
        np.maximum.at(hi, tcomp, P.max(axis=1))
        ntri = np.bincount(tcomp, minlength=ncomp)
        size = hi - lo
        # global triangle -> component, for the ray hits
        comp_of = np.full(len(D.F), -1, dtype=np.int64)
        comp_of[near] = tcomp
        self.comp_of, self.comp_lo, self.comp_hi = comp_of, lo, hi
        first_tri = np.full(ncomp, -1, dtype=np.int64)
        first_tri[tcomp[::-1]] = near[::-1]
        diag = np.linalg.norm(size, axis=1)
        land = np.array([any(w in D.surf[D.sid[t]]["name"] for w in LAND_WORDS) for t in first_tri])
        cand = np.nonzero((diag > 0.6) & (diag < 400.0) & ~land & (lo[:, 1] > -20))[0]
        self.stats["components"] = int(ncomp)
        # Lowest points of each candidate, rays straight down.
        flo, short = [], []
        tri_c = P.mean(axis=1)
        order = np.argsort(tcomp, kind="stable")
        starts = np.searchsorted(tcomp[order], np.arange(ncomp))
        ends = np.searchsorted(tcomp[order], np.arange(ncomp), side="right")
        origins, owners = [], []
        for c in cand:
            ids = order[starts[c]:ends[c]]
            pts = P[ids].reshape(-1, 3)
            low = pts[pts[:, 1] < lo[c, 1] + max(0.05, 0.03 * size[c, 1])]
            if len(low) > 12:
                low = low[np.linspace(0, len(low) - 1, 12).astype(int)]
            origins.append(low - np.array([0, 0.005, 0]))
            owners.append(np.full(len(low), c))
        if not origins:
            return
        O = np.concatenate(origins)
        own = np.concatenate(owners)
        idx, loc, dist = self.first(O, np.tile([0, -1, 0], (len(O), 1)))
        hit_src = self.src(idx)
        hit_comp = np.where(hit_src >= 0, comp_of[np.maximum(hit_src, 0)], -2)
        dist = np.where(idx < 0, INF, dist)
        gap = defaultdict(lambda: INF)
        selfsup = Counter()
        for c, hc, dd in zip(own, hit_comp, dist):
            if hc == c:
                selfsup[c] += 1
                continue
            gap[c] = min(gap[c], dd)
        # Lateral contact: any other piece's vertex or face within 12 cm of this piece.
        allv = P.reshape(-1, 3)
        allc = np.repeat(tcomp, 3)
        tree = cKDTree(allv)
        floating = []
        for c in cand:
            gp = gap[c]
            if gp < 0.08:
                continue
            ids = order[starts[c]:ends[c]]
            pts = P[ids].reshape(-1, 3)
            if len(pts) > 300:
                pts = pts[np.linspace(0, len(pts) - 1, 300).astype(int)]
            touch = False
            for nb in tree.query_ball_point(pts, 0.12):
                if any(allc[j] != c for j in nb):
                    touch = True
                    break
            if not touch:
                # faces of others close by, by short rays both ways along x, z and up
                o = np.repeat(pts[:60], 5, axis=0)
                dirs = np.tile([[1, 0, 0], [-1, 0, 0], [0, 0, 1], [0, 0, -1], [0, 1, 0]], (min(60, len(pts)), 1))
                hi_ids, ray_ids, locs = self.ray.intersects_id(o, dirs.astype(float), multiple_hits=True, return_locations=True)
                if len(hi_ids):
                    dd = np.linalg.norm(locs - o[ray_ids], axis=1)
                    hs = self.src(hi_ids)
                    hc = np.where(hs >= 0, comp_of[np.maximum(hs, 0)], -2)
                    if np.any((hc != c) & (dd < 0.15)):
                        touch = True
            tall_thin = size[c, 1] > 1.2 and max(size[c, 0], size[c, 2]) < 0.9
            if touch:
                if tall_thin and 0.04 < gp < 3.0:
                    short.append((c, gp))
                continue
            floating.append((c, gp))
        self.stats["floating_raw"] = len(floating)
        floating = [(c, g) for c, g in floating if not np.isfinite(g) or g > 0.3]
        # one finding a kind of piece (same part, material and size), its places listed
        def sig(c):
            t = first_tri[c]
            sf = D.surf[D.sid[t]]
            return (top_name(sf["node"]), sf["material"].get("name", ""), tuple(np.round(size[c] * 2) / 2))
        for lst, check in ((floating, "floating"), (short, "short_leg")):
            kinds = defaultdict(list)
            for c, gp in lst:
                kinds[sig(c)].append((c, gp))
            order_k = sorted(kinds.items(), key=lambda kv: -float(np.linalg.norm(kv[0][2])) * len(kv[1]) ** 0.5)
            for (top, matn, sz), items in order_k[:30]:
                pts = np.array([(lo[c] + hi[c]) / 2 if check == "floating" else
                                [(lo[c, 0] + hi[c, 0]) / 2, lo[c, 1], (lo[c, 2] + hi[c, 2]) / 2] for c, _ in items])
                gaps = np.array([g for _, g in items])
                fin = gaps[np.isfinite(gaps)]
                gtxt = ("%.2f to %.2f m above the surface under it" % (fin.min(), fin.max())) if len(fin) else "nothing under it"
                if len(fin) and len(fin) < len(gaps):
                    gtxt += " (some have nothing under them)"
                c0 = items[0][0]
                vd = max(8.0, float(np.linalg.norm(size[c0])) * 1.6)
                if check == "floating":
                    title = "Floating object (touches nothing)"
                    what = "%.1f x %.1f x %.1f m pieces of %s (material %s) that touch nothing, %s" % (
                        sz[0], sz[1], sz[2], top, matn, gtxt)
                    cause = "Placed at the wrong height, its support left out, or left behind when the part under it moved."
                else:
                    title = "Legs or posts stop short of the floor"
                    what = "%.1f m tall posts of %s (material %s) ending %s" % (sz[1], top, matn, gtxt)
                    cause = "Post length not cut to the deck or ground it stands on."
                self._cluster_report(pts, check, title, what, cause, min_n=1, cell=15.0, bowl=False,
                                     view_fn=lambda p, vd=vd: self.close_view(p, None, vd))

    # 3. Seats -------------------------------------------------------------------------------------
    def seat_sets(self):
        """Every seat: (position at the middle of its pan, colour, forward dir, up dir, scale)."""
        out = []
        pts = np.array(self.D.g.get("seat_points") or [[0, 0.45, 0]], float)
        mid = pts.mean(axis=0)
        mid[1] = 0.0
        for m in self.D.mms:
            nm = m["node"].split("/")[-1]
            if not nm.startswith("seats_") or nm.endswith("_far"):
                continue
            colour = nm[len("seats_"):].rsplit("_", 1)[0]
            W, faces = self.D.mm(m)
            if len(W) == 0:
                continue
            p = (W[:, :3, :3] @ mid) + W[:, :3, 3]
            out.append({"colour": colour, "p": p, "basis": W[:, :3, :3], "node": m["node"], "far": False})
        return out

    def check_seats(self):
        sets = self.seat_sets()
        model_seats = [k for k, s in enumerate(self.D.surf) if "seat" in s["name"] and s["cat"] == "model"]
        self.stats["seat_multimeshes"] = len(sets)
        self.stats["model_seat_surfaces"] = len(model_seats)
        P, C, Bs = [], [], []
        for s in sets:
            P.append(s["p"])
            C += [s["colour"]] * len(s["p"])
            Bs.append(s["basis"])
        if model_seats and self.__dict__.get("comp_of") is not None:
            # seats built into the model: one connected piece a seat
            D = self.D
            for k in model_seats:
                sel = np.nonzero(D.sid == k)[0]
                comps = self.comp_of[sel]
                comps = comps[comps >= 0]
                if len(comps) == 0:
                    continue
                uc = np.unique(comps)
                ctr = (self.comp_lo[uc] + self.comp_hi[uc]) / 2
                small = np.linalg.norm(self.comp_hi[uc] - self.comp_lo[uc], axis=1) < 1.5
                P.append(ctr[small])
                C += [D.surf[k]["material"].get("name", str(k))] * int(small.sum())
        if not P:
            self.stats["seats"] = 0
            return
        P = np.concatenate(P)
        C = np.array(C)
        self.seats_p, self.seats_c = P, C
        self.stats["seats"] = int(len(P))
        log("seats: %d" % len(P))
        # (a) colours mixed at random: share of a seat's 8 nearest neighbours in another colour.
        if len(np.unique(C)) > 1 and len(P) > 50:
            tree = cKDTree(P)
            d, nb = tree.query(P, k=9, distance_upper_bound=1.6)
            nb = nb[:, 1:]
            valid = nb < len(P)
            other = (C[np.minimum(nb, len(P) - 1)] != C[:, None]) & valid
            share = other.sum(axis=1) / np.maximum(1, valid.sum(axis=1))
            self.stats["seat_colour_mismatch_mean"] = round(float(share.mean()), 3)
            bad = share > 0.3
            # a seat counts when it and most of its block are mixed: smooth the share over 4 m
            nbs = tree.query_ball_point(P, 4.0)
            sm = np.array([share[n].mean() for n in nbs])
            sel = np.nonzero(sm > 0.3)[0]
            mix = Counter(C[sel]).most_common()
            self._cluster_report(P[sel], "seat_colours_random", "Seat colours mixed at random",
                                 "seats in blocks where on average over 30%% of each seat's neighbours are another colour "
                                 "(%s; real stands lay colours in blocks, bands or a pattern)" % ", ".join("%s %d" % t for t in mix),
                                 "The seat builder picks a colour per seat (noise or random), not the real pattern.", min_n=20)
        # (b) seats standing wrong: tipped, huge, facing away, off their tread, inside something
        if Bs:
            B = np.concatenate(Bs)
            n0 = sum(len(s["p"]) for s in sets)
            Pm = P[:n0]
            up = B[:, :, 1]
            sc = np.linalg.norm(B, axis=1)  # column lengths
            upn = up / np.maximum(1e-9, np.linalg.norm(up, axis=1, keepdims=True))
            tilt = np.degrees(np.arccos(np.clip(upn[:, 1], -1, 1)))
            fwd = B[:, :, 2] / np.maximum(1e-9, np.linalg.norm(B[:, :, 2], axis=1, keepdims=True))
            to_mid = -Pm.copy()
            to_mid[:, 1] = 0
            to_mid /= np.maximum(1e-9, np.linalg.norm(to_mid, axis=1, keepdims=True))
            face = np.einsum("ij,ij->i", fwd, to_mid)
            med = np.median(sc, axis=0)
            big = np.nonzero((sc > med * 1.6).any(axis=1))[0]
            tipped = np.nonzero(tilt > 25)[0]
            self._cluster_report(Pm[tipped], "seat_tipped", "Seats tipped over or standing on end",
                                 "seats whose upright leans more than 25 deg", "Wrong seat transform (a row's slope or a stale file).")
            self._cluster_report(Pm[big], "seat_huge", "Seats drawn far too big",
                                 "seats scaled more than 1.6x the ground's usual seat", "Wrong seat transform scale.")
            # which way is "forward" for this template: whichever most seats agree on
            sgn = 1.0 if np.median(face) >= 0 else -1.0
            away = np.nonzero(face * sgn < -0.3)[0]
            self._cluster_report(Pm[away], "seat_backwards", "Seats facing away from the field",
                                 "seats turned more than 107 deg from the field", "Seat yaw flipped for this block.")
            self.stats["seat_tilt_p99"] = round(float(np.percentile(tilt, 99)), 1)
        # (c) off their treads, buried, inside the fence
        step = max(1, len(P) // 20000)
        S = P[::step]
        idx, loc, dist = self.first(S + [0, 0.25, 0], np.tile([0, -1, 0], (len(S), 1)))
        drop = np.where(idx >= 0, dist - 0.25, INF)
        med = float(np.median(drop[np.isfinite(drop)])) if np.isfinite(drop).any() else 0.0
        self.stats["seat_drop_median"] = round(med, 3)
        fl = np.nonzero(drop > max(0.35, med + 0.3))[0]
        self._cluster_report(S[fl], "seat_off_tread", "Seats floating above their tread",
                             "seats standing at least 30 cm higher off the floor than the ground's usual seat (median %.2f m)" % med,
                             "Seat rows not following the stand's real rake (the seat file and the model disagree).", extra_vals=drop[fl])
        idx2, loc2, dist2 = self.first(S + [0, 0.3, 0], np.tile([0, 1, 0], (len(S), 1)))
        bur = np.nonzero((idx2 >= 0) & (dist2 < 0.8))[0]
        self._cluster_report(S[bur], "seat_buried", "Seats with the stand through them",
                             "seats with model geometry less than 1.1 m above the pan", "Seats placed inside a step, wall or the tier above.")
        inside = np.nonzero((S[:, 0] / self.fx) ** 2 + (S[:, 2] / self.fz) ** 2 < 1.0)[0]
        self._cluster_report(S[inside], "seat_in_fence", "Seats inside the boundary fence",
                             "seats inside the match's fence", "Seat file or fit puts a row on the arena.")
        # (d) far-LOD seat quads
        for m in self.D.mms:
            nm = m["node"].split("/")[-1]
            if nm.endswith("_far") and nm.startswith("seats_"):
                if float(m.get("vis_begin", 0)) < 30.0 and not self.D.g.get("seat_far"):
                    self.add("seat_far_near", "Far-away seat cards drawn up close", [0, 0, 0],
                             "%s draws the flat far-seat cards from %.0f m." % (nm, m.get("vis_begin", 0)),
                             "SEAT_FAR fade distances.")

    def _seat_view(self, p):
        p = np.asarray(p, float)
        h = np.array([-p[0], 0, -p[2]])
        h /= np.linalg.norm(h) + 1e-9
        eye = p + h * 18 + np.array([0, 6, 0])
        return (eye, p, 50.0)

    def _groups(self, pts, cell, bowl):
        if bowl:
            bear = (np.degrees(np.arctan2(pts[:, 2], pts[:, 0])) % 360) // 10
            band = np.floor(pts[:, 1] / 6.0)
            keys = list(zip(bear.astype(int), band.astype(int)))
            cl = defaultdict(list)
            for i, k in enumerate(keys):
                cl[k].append(i)
            return sorted(cl.values(), key=len, reverse=True)
        key = np.floor(pts / cell).astype(int)
        cl = defaultdict(list)
        for i, k in enumerate(map(tuple, key)):
            cl[(k[0], k[2])].append(i)
        groups, seen = [], set()
        for k in cl:
            if k in seen:
                continue
            stack, g = [k], []
            seen.add(k)
            while stack:
                a = stack.pop()
                g += cl[a]
                for dx in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        b2 = (a[0] + dx, a[1] + dz)
                        if b2 in cl and b2 not in seen:
                            seen.add(b2)
                            stack.append(b2)
            groups.append(g)
        return sorted(groups, key=len, reverse=True)

    def _cluster_report(self, pts, check, title, what, cause, extra_vals=None, min_n=3, cell=6.0, limit=12,
                        bowl=None, view_fn=None, severity="fault"):
        """One finding for every spot of one kind: the places listed, the worst three filmed."""
        pts = np.asarray(pts, float).reshape(-1, 3)
        self.stats[check] = self.stats.get(check, 0) + int(len(pts))
        if len(pts) == 0:
            return
        if bowl is None:
            bowl = check.startswith("seat") or check in ("sky_gap", "leg_huge", "leg_no_seat")
        groups = [g for g in self._groups(pts, cell, bowl) if len(g) >= min_n]
        if not groups:
            return
        view_fn = view_fn or self._seat_view
        places, views = [], []
        for g in groups[:limit]:
            q = pts[g]
            ctr = q[np.argmin(np.linalg.norm(q - q.mean(axis=0), axis=1))]
            span = q.max(axis=0) - q.min(axis=0)
            ev = ""
            if extra_vals is not None:
                ev = ", worst %.2f m" % float(np.max(np.asarray(extra_vals)[g]))
            bear = math.degrees(math.atan2(ctr[2], ctr[0])) % 360
            places.append({"where": where(ctr), "count": len(g), "span_m": [round(float(span[0])), round(float(span[2]))],
                           "note": "%d over %.0f x %.0f m%s (bearing %d deg from the centre, %.0f m up)" % (
                               len(g), span[0], span[2], ev, bear, ctr[1])})
            if len(views) < 3:
                views.append(view_fn(ctr))
        n_in = sum(len(g) for g in groups)
        ctr0 = pts[groups[0]][np.argmin(np.linalg.norm(pts[groups[0]] - pts[groups[0]].mean(axis=0), axis=1))]
        self.add(check, title, ctr0, "%d %s, in %d places%s." % (
            n_in, what, len(groups), " (the %d biggest listed)" % limit if len(groups) > limit else ""), cause,
            severity=severity, view=views[0], more_views=views[1:], extra={"places": places})

    def check_legs(self):
        if not self.leg_info:
            return
        seats = getattr(self, "seats_p", None)
        allp, alls = [], []
        for m, W, faces in self.leg_info:
            lo, hi = faces.min(axis=0), faces.max(axis=0)
            corners = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
            cw = np.einsum("nij,kj->nki", W[:, :3, :], corners)
            allp.append(cw.mean(axis=1))
            alls.append(cw.max(axis=1) - cw.min(axis=1))
        P = np.concatenate(allp)
        S = np.concatenate(alls)
        self.stats["legs"] = int(len(P))
        med = np.median(S, axis=0)
        huge = np.nonzero((S > np.maximum(med * 2.5, med + 0.6)).any(axis=1))[0]
        self._cluster_report(P[huge], "leg_huge", "Seat legs drawn as huge slabs",
                             "seat legs more than 2.5 times the usual leg's size (dark slabs or fins)",
                             "Leg transforms from a stale legs file (built for an older bowl).")
        if seats is not None and len(seats):
            d, _ = cKDTree(seats).query(P, k=1)
            lone = np.nonzero(d > 1.0)[0]
            self.stats["legs_without_seat"] = int(len(lone))
            self._cluster_report(P[lone], "leg_no_seat", "Seat legs with no seat on them",
                                 "seat legs more than 1 m from any seat", "Legs file out of step with the seats file (stale).")
        inside = np.nonzero((P[:, 0] / self.fx) ** 2 + (P[:, 2] / self.fz) ** 2 < 1.0)[0]
        self._cluster_report(P[inside], "leg_over_field", "Seat legs over the field",
                             "seat legs inside the boundary fence", "Stale or misplaced legs file.", min_n=1)

    # 4. Seats open to the sky through gaps between roof, fascia and stand -----------------------------
    def check_sky(self):
        P = getattr(self, "seats_p", None)
        if P is None or len(P) < 50:
            return
        step = max(1, len(P) // 15000)
        S = P[::step]
        O = S + [0, 1.2, 0]
        _, _, dup = self.first(O, np.tile([0, 1, 0], (len(S), 1)))
        out = np.c_[S[:, 0], np.zeros(len(S)), S[:, 2]]
        out /= np.maximum(1e-9, np.linalg.norm(out, axis=1, keepdims=True))
        back = out * math.sin(math.radians(30)) + np.array([0, math.cos(math.radians(30)), 0])
        _, _, dbk = self.first(O, back)
        open_up = ~np.isfinite(dup)
        open_bk = ~np.isfinite(dbk)
        self.stats["seats_open_up_share"] = round(float(open_up.mean()), 3)
        tree = cKDTree(S)
        nb = tree.query_ball_point(S, 5.0)
        gaps = []
        for i in np.nonzero(open_up | open_bk)[0]:
            n = [j for j in nb[i] if j != i]
            if len(n) < 6:
                continue
            cov = np.mean(~open_up[n]) if open_up[i] else np.mean(~open_bk[n])
            if cov >= 0.65:
                gaps.append(i)
        self._cluster_report(S[gaps], "sky_gap", "Seats open to the sky through a gap in the roof",
                             "seats that see the sky (straight up, or up and back) while the seats round them are covered",
                             "A gap between roof panels, or between the roof, its fascia and the stand behind.", min_n=2)

    # 5. Trees: on roofs, floating, inside buildings, generic shapes ---------------------------------
    def check_trees(self):
        trunks = []
        for m in self.D.mms:
            nm = m["node"].split("/")[-1]
            if nm.startswith("Trunks") or nm.startswith("Trees") and not nm.startswith("TreesFar"):
                W, faces = self.D.mm(m)
                if len(W) == 0:
                    continue
                if nm.startswith("Trunks"):
                    # trunk cylinder of height 1 centred: base is origin - 0.5*up
                    base = W[:, :3, 3] - 0.5 * W[:, :3, 1]
                    trunks.append(base)
        self.stats["tree_instances"] = int(sum(len(t) for t in trunks))
        if trunks:
            B = np.concatenate(trunks)
            near = B[np.hypot(B[:, 0], B[:, 2]) < 900]
            if len(near):
                idx, loc, dist = self.first(near + [0, 80, 0], np.tile([0, -1, 0], (len(near), 1)))
                src = self.src(idx)
                top_h = near[:, 1] + 80 - dist
                hitcat = np.array([self.D.surf[self.D.sid[s]]["name"] if s >= 0 else "" for s in src])
                onroof = np.nonzero((top_h > near[:, 1] + 2.5) & np.array([not any(w in h for w in LAND_WORDS + TREE_WORDS) for h in hitcat]))[0]
                self._cluster_report(near[onroof], "tree_on_roof", "Trees standing on or through a roof",
                                     "trees whose trunk base is under a roof or building top more than 2.5 m above it",
                                     "Tree positions from a canopy map include roofs (or the building moved); the tree is "
                                     "not cut where a building stands.", min_n=1, cell=10.0, bowl=False,
                                     view_fn=lambda p: (p + np.array([25, 20, 25]), p, 55.0))
                idx3, loc3, d3 = self.first(near + [0, 0.3, 0], np.tile([0, -1, 0], (len(near), 1)))
                fl = np.nonzero(np.where(idx3 >= 0, d3 - 0.3, INF) > 0.6)[0]
                self._cluster_report(near[fl], "tree_floating", "Trees floating above the ground",
                                     "trees whose trunk base is more than 60 cm above the ground under it",
                                     "Tree heights taken from flat land, not the real terrain.", min_n=1, cell=10.0, bowl=False,
                                     view_fn=lambda p: (p + np.array([15, 6, 15]), p, 55.0))
        # backdrop trees as meshes: cone-shaped crowns or one tree model repeated
        comp_lo = getattr(self, "comp_lo", None)
        if comp_lo is None:
            return
        D = self.D
        tree_surf = [k for k, s in enumerate(D.surf) if any(w in s["name"] for w in TREE_WORDS) and s["cat"] != "oval"]
        self.stats["tree_mesh_surfaces"] = len(tree_surf)
        sig = Counter()
        cone = []
        for k in tree_surf:
            sel = np.nonzero(D.sid == k)[0]
            comps = np.unique(self.comp_of[sel])
            comps = comps[comps >= 0]
            sz = self.comp_hi[comps] - self.comp_lo[comps]
            for c, s in zip(comps, sz):
                sig[(k, round(s[0], 1), round(s[1], 1), round(s[2], 1))] += 1
        rep = [(k, n) for k, n in sig.items() if n >= 25]
        for (k, sx, sy, sz), n in sorted(rep, key=lambda t: -t[1])[:5]:
            self.add("generic_trees", "One tree model copied many times", [0, 0, 0],
                     "%d trees in %s are the same %.1f x %.1f x %.1f m model (same size and shape)." % (
                         n, D.surf[k]["node"], sx, sy, sz),
                     "Trees placed from a single library model, not varied to the real species and sizes.",
                     severity="look")

    # 6. The model's place against the real map, and roads under the stadium or buildings -------------
    def check_frame_and_roads(self):
        if not self.osm:
            self.stats["osm"] = "missing"
            return
        feats = self.osm["features"]
        axis = float(self.D.g["axis"])
        # the model's footprint: plan cells where the model stands 3 m or more above the turf
        cells = 2.0
        D = self.D
        mod = np.nonzero(D.cat == "model")[0]
        hi_tri = mod[self.tri[mod][:, :, 1].max(axis=1) > 3.0]
        pc = self.cen[hi_tri]
        pc = pc[np.hypot(pc[:, 0], pc[:, 2]) < 400]
        if len(pc) == 0:
            return
        foot = set(map(tuple, np.floor(pc[:, [0, 2]] / cells).astype(int)))
        stad = [f for f in feats if f["tags"].get("leisure") == "stadium" or f["tags"].get("building") == "stadium"]
        best = None
        try:
            from shapely.geometry import Polygon, Point
            from shapely.ops import unary_union
            for mirror in (False, True):
                polys = []
                for f in stad:
                    if len(f["pts"]) >= 4:
                        pts = [enu_to_world(e, n, axis, mirror) for e, n in f["pts"]]
                        pg = Polygon(pts).buffer(0)
                        if pg.area > 5000 and pg.distance(Point(0, 0)) < 50:
                            polys.append(pg)
                if not polys:
                    continue
                pg = unary_union(polys)
                minx, minz, maxx, maxz = pg.bounds
                hit = 0
                tot = 0
                for (i, j) in foot:
                    tot += 1
                    if pg.contains(Point((i + 0.5) * cells, (j + 0.5) * cells)):
                        hit += 1
                inside_cells = 0
                for i in range(int(minx // cells), int(maxx // cells) + 1):
                    for j in range(int(minz // cells), int(maxz // cells) + 1):
                        if pg.contains(Point((i + 0.5) * cells, (j + 0.5) * cells)):
                            inside_cells += 1
                iou = hit / max(1, tot + inside_cells - hit)
                fc = np.array(list(foot)).mean(axis=0) * cells
                off = (fc[0] - pg.centroid.x, fc[1] - pg.centroid.y)
                cand = {"mirror": mirror, "iou": round(iou, 3), "offset": [round(off[0], 1), round(off[1], 1)]}
                if best is None or iou > best["iou"]:
                    best = cand
                self.stats.setdefault("frame_fit", []).append(cand)
        except ImportError:
            pass
        self.mirror = bool(best["mirror"]) if best else False
        if best:
            self.stats["frame"] = best
            if best["mirror"]:
                self.add("frame_mirrored", "The ground and its surrounds are mirror-image of the real place", [0, 0, 0],
                         "The model's outline matches the real stadium outline (OpenStreetMap) only when the map is flipped "
                         "across the ground's long axis (overlap %.0f%% flipped vs %.0f%% as it is)." % (
                             100 * best["iou"], 100 * min(x["iou"] for x in self.stats["frame_fit"])),
                         "The model and its surrounds were built in a mirrored frame (the inspector's z runs the wrong way).")
            off = math.hypot(*best["offset"])
            if off > 6.0:
                self.add("model_offset", "Stadium sits off its real position", [best["offset"][0], 0, best["offset"][1]],
                         "The model's footprint centre is %.1f m from the real stadium outline's centre (x %+.1f, z %+.1f), "
                         "with the map %s." % (off, best["offset"][0], best["offset"][1], "flipped" if best["mirror"] else "as it is"),
                         "Model centre (grounds.json lat/lon or the FIT row) does not match the real stadium.")
        # Roads under the stadium or under buildings (OSM roads, sampled every 2 m).
        road_kinds = {"motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "residential",
                      "service", "living_street", "pedestrian", "footway", "cycleway", "path", "primary_link",
                      "secondary_link", "tertiary_link", "trunk_link", "busway", "steps"}
        samples, info = [], []
        for f in feats:
            t = f["tags"]
            if t.get("highway") not in road_kinds and "railway" not in t:
                continue
            if t.get("tunnel") or t.get("covered") in ("yes",) or t.get("layer", "0").startswith("-") or t.get("indoor"):
                continue
            if t.get("bridge") and t.get("bridge") != "no":
                continue
            if t.get("railway") in ("platform",):
                continue
            pts = [enu_to_world(e, n, axis, self.mirror) for e, n in f["pts"]]
            for a, b in zip(pts[:-1], pts[1:]):
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                for k in range(max(1, int(L / 2.0))):
                    u = k / max(1, int(L / 2.0))
                    x, z = a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
                    if math.hypot(x, z) < 650:
                        samples.append((x, z))
                        info.append(f)
        if not samples:
            return
        S = np.array(samples)
        O = np.c_[S[:, 0], np.full(len(S), 250.0), S[:, 1]]
        idx, loc, dist = self.first(O, np.tile([0, -1, 0], (len(S), 1)))
        src = self.src(idx)
        # the land under the same spot: the lowest hit going down
        hi_ids, ray_ids, locs = self.ray.intersects_id(O, np.tile([0, -1.0, 0], (len(S), 1)), multiple_hits=True,
                                                         return_locations=True)
        low = np.full(len(S), np.nan)
        if len(ray_ids):
            order = np.lexsort((locs[:, 1], ray_ids))
            r_sorted = ray_ids[order]
            first_idx = np.r_[0, np.nonzero(np.diff(r_sorted))[0] + 1]
            low[r_sorted[first_idx]] = locs[order][first_idx, 1]
        top = loc[:, 1]
        over = top - low
        on_model, on_bld = [], []
        for i in range(len(S)):
            if src[i] < 0 or not np.isfinite(over[i]) or over[i] < 2.5:
                continue
            s = D.surf[D.sid[src[i]]]
            nm = s["name"]
            if any(w in nm for w in TREE_WORDS):
                continue
            if s["cat"] == "model":
                on_model.append(i)
            elif not any(w in nm for w in LAND_WORDS):
                on_bld.append(i)
        self.stats["road_samples"] = int(len(S))
        for check, sel, title, cause in (
                ("stadium_on_road", on_model, "Stadium stands on a real road or footpath",
                 "The stadium model, its footprint or the road layer is in the wrong place (centre, bearing or size)."),
                ("building_on_road", on_bld, "Building stands on a real road or footpath",
                 "Surrounding building placed or extruded over the road (footprint offset, or a shelter or canopy over the "
                 "road built as a solid block).")):
            if not sel:
                continue
            pts3 = np.c_[S[sel, 0], top[sel], S[sel, 1]]
            names = Counter(info[i]["tags"].get("name") or info[i]["tags"].get("highway") or info[i]["tags"].get("railway") for i in sel)
            self._cluster_report(pts3, check, title, "2 m samples of real roads and paths (%s) that have %s standing over them" % (
                ", ".join("%s" % n for n, _ in names.most_common(4)), "the stadium" if check == "stadium_on_road" else "a building"),
                cause, cell=8.0, min_n=2, bowl=False, view_fn=lambda p: (p + np.array([30, 25, 30]), p, 55.0))

    # 7. Real structures missing: bridges and footbridges, big buildings --------------------------------
    def check_osm_structures(self):
        if not self.osm:
            return
        D = self.D
        axis = float(D.g["axis"])
        mirror = getattr(self, "mirror", False)
        for f in self.osm["features"]:
            t = f["tags"]
            is_bridge = (t.get("bridge") not in (None, "no")) or t.get("man_made") == "bridge"
            if not is_bridge or t.get("waterway"):
                continue
            pts = [enu_to_world(e, n, axis, mirror) for e, n in f["pts"]]
            if not pts or min(math.hypot(x, z) for x, z in pts) > 700:
                continue
            samp = []
            for a, b in zip(pts[:-1], pts[1:]):
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                n = max(1, int(L / 3))
                for k in range(n):
                    u = (k + 0.5) / n
                    samp.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
            if len(samp) < 3:
                continue
            # the middle of the span, away from its ends where it meets the land
            mid = samp[len(samp) // 4: max(len(samp) // 4 + 1, 3 * len(samp) // 4)]
            S = np.array(mid)
            O = np.c_[S[:, 0], np.full(len(S), 250.0), S[:, 1]]
            hi_ids, ray_ids, locs = self.ray.intersects_id(O, np.tile([0, -1.0, 0], (len(S), 1)), multiple_hits=True,
                                                             return_locations=True)
            has_deck = 0
            for i in range(len(S)):
                ys = np.sort(locs[ray_ids == i, 1])
                if len(ys) >= 2 and ys[-1] - ys[0] > 2.5:
                    has_deck += 1
            if has_deck < 0.4 * len(S):
                name = t.get("name") or t.get("highway") or t.get("railway") or "bridge"
                c = np.array(mid[len(mid) // 2])
                y = 0.0
                ii, ll, dd = self.first([[c[0], 250, c[1]]], [[0, -1, 0]])
                if np.isfinite(ll[0, 1]):
                    y = ll[0, 1]
                p = np.array([c[0], y + 6, c[1]])
                self.add("missing_bridge", "Real bridge or walkway missing", p,
                         "OpenStreetMap has %s (%s, %s, %d m) crossing here; the ground has no deck over it at %d of %d points along its middle." % (
                             name, t.get("highway") or t.get("railway") or t.get("man_made"), f["id"],
                             int(sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts[:-1], pts[1:]))),
                             len(S) - has_deck, len(S)),
                         "Not modelled: the surrounds builder treats bridges as land (terrain README: decks must be built as structures).",
                         view=(p + np.array([40, 25, 40]), p, 55.0), extra={"osm": f["id"]})
        # big real buildings with nothing standing there
        try:
            from shapely.geometry import Polygon
        except ImportError:
            return
        miss = []
        for f in self.osm["features"]:
            t = f["tags"]
            if "building" not in t or t.get("building") in ("roof", "no", "construction") or len(f["pts"]) < 4:
                continue
            pts = [enu_to_world(e, n, axis, mirror) for e, n in f["pts"]]
            pg = Polygon(pts).buffer(0)
            if pg.area < 250 or pg.is_empty:
                continue
            c = pg.representative_point()
            r = math.hypot(c.x, c.y)
            if r > 600 or r < 30:
                continue
            miss.append((f, pg, c))
        if miss:
            O = np.array([[c.x, 250.0, c.y] for _, _, c in miss])
            hi_ids, ray_ids, locs = self.ray.intersects_id(O, np.tile([0, -1.0, 0], (len(O), 1)), multiple_hits=True,
                                                             return_locations=True)
            for i, (f, pg, c) in enumerate(miss):
                ys = np.sort(locs[ray_ids == i, 1])
                if len(ys) == 0 or ys[-1] - ys[0] < 2.0:
                    t = f["tags"]
                    y = float(ys[0]) if len(ys) else 0.0
                    p = np.array([c.x, y + 3, c.y])
                    self.add("missing_building", "Real building missing (empty ground where it stands)", p,
                             "OpenStreetMap has a %s building%s of %.0f m2 here (%s); nothing stands higher than 2 m on its spot." % (
                                 t.get("building"), (" '%s'" % t["name"]) if t.get("name") else "", pg.area, f["id"]),
                             "Building left out of the surrounds (or the surrounds were built from older or different data).",
                             view=(p + np.array([35, 30, 35]), p, 55.0), extra={"osm": f["id"]})

    # 8. Building outlines: shelters built as solid blocks, jagged or self-crossing outlines -----------
    def check_buildings(self):
        if not self.osm:
            return
        try:
            from shapely.geometry import Polygon
        except ImportError:
            return
        D = self.D
        axis = float(D.g["axis"])
        mirror = getattr(self, "mirror", False)
        open_kinds = {"roof", "canopy", "carport", "shelter", "pavilion", "bandstand", "grandstand", "kiosk_roof"}
        for f in self.osm["features"]:
            t = f["tags"]
            kind = t.get("building") or t.get("building:part")
            if not (kind in open_kinds or t.get("amenity") == "shelter" or t.get("covered") == "yes" and "building" in t):
                continue
            if len(f["pts"]) < 4:
                continue
            pg = Polygon([enu_to_world(e, n, axis, mirror) for e, n in f["pts"]]).buffer(0)
            if pg.is_empty or pg.area < 12:
                continue
            c = pg.representative_point()
            if math.hypot(c.x, c.y) > 650:
                continue
            ii, ll, dd = self.first([[c.x, 250, c.y]], [[0, -1, 0]])
            if not np.isfinite(ll[0, 1]):
                continue
            # the land: lowest hit
            hi_ids, ray_ids, locs = self.ray.intersects_id(np.array([[c.x, 250.0, c.y]]), np.array([[0, -1.0, 0]]),
                                                             multiple_hits=True, return_locations=True)
            if len(locs) == 0:
                continue
            y0 = float(locs[:, 1].min())
            top = float(locs[:, 1].max())
            if top - y0 < 2.0:
                continue
            o = np.array([c.x, y0 + 1.3, c.y])
            reach = math.sqrt(pg.area) * 0.75
            dirs = np.array([[math.cos(a), 0, math.sin(a)] for a in np.radians(np.arange(0, 360, 45))])
            idx, loc, dist = self.first(np.tile(o, (8, 1)), dirs)
            walls = int(np.sum(dist < reach))
            if walls >= 6:
                self.add("solid_shelter", "Open shelter or canopy built as a solid block", o,
                         "OpenStreetMap marks this as an open %s (%s, %.0f m2)%s; in the ground it is closed: walls within %.0f m in %d of 8 directions at head height." % (
                             kind or "shelter", f["id"], pg.area, (" '%s'" % t["name"]) if t.get("name") else "", reach, walls),
                         "The surrounds builder extrudes every footprint as a solid box, including roofs on posts.",
                         view=(o + np.array([25, 14, 25]), o, 55.0), extra={"osm": f["id"]})
        # outlines in the game: roof shapes of the surrounds' and backdrop's buildings
        comp_of = getattr(self, "comp_of", None)
        if comp_of is None:
            return
        cand = np.nonzero(((D.cat == "surrounds") | (D.cat == "backdrop"))
                          & (np.hypot(self.cen[:, 0], self.cen[:, 2]) < 600) & (comp_of >= 0))[0]
        names = [D.surf[D.sid[t]]["name"] for t in cand[:1]]
        P = self.tri[cand]
        e1, e2 = P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]
        cr = np.cross(e1, e2)
        ar = 0.5 * np.linalg.norm(cr, axis=1)
        ny = -cr[:, 1] / np.maximum(1e-9, 2 * ar)
        flat = np.abs(ny) > 0.9
        notland = np.array([not any(w in D.surf[D.sid[t]]["name"] for w in LAND_WORDS + TREE_WORDS) for t in cand])
        sel = flat & notland & (ar > 0.01)
        comp = comp_of[cand[sel]]
        ys = P[sel][:, :, 1].mean(axis=1)
        bad = []
        by = defaultdict(list)
        for i, c in enumerate(comp):
            by[c].append(i)
        idxs = np.nonzero(sel)[0]
        for c, ii in by.items():
            if len(ii) < 2:
                continue
            ii = np.array(ii)
            topy = ys[ii].max()
            if topy - self.comp_lo[c][1] < 2.5:
                continue
            roof = ii[ys[ii] > topy - 0.3]
            tri2 = P[idxs[roof]][:, :, [0, 2]]
            down = np.sum(ny[idxs[roof]] < 0)
            area_sum = ar[idxs[roof]].sum()
            if area_sum < 20:
                continue
            try:
                from shapely.ops import unary_union
                u = unary_union([Polygon(t).buffer(0.001) for t in tri2])
            except Exception:  # noqa: BLE001
                continue
            if u.is_empty:
                continue
            overlap = area_sum / max(1e-6, u.area)
            hull = u.convex_hull
            per = u.length if u.geom_type == "Polygon" else sum(g.length for g in u.geoms)
            jag = per / max(1e-6, 4 * math.sqrt(u.area))
            ctr = u.representative_point()
            pt = [ctr.x, topy, ctr.y]
            if overlap > 1.25 or (down > 0 and down >= 0.3 * len(roof)):
                bad.append(("overlap", c, pt, overlap, down, len(roof), jag))
            elif jag > 2.2 and u.area < 0.7 * hull.area and u.area > 60:
                bad.append(("jagged", c, pt, overlap, down, len(roof), jag))
        self.stats["building_roofs_checked"] = len(by)
        for kind, c, pt, ov, down, n, jag in bad[:40]:
            if kind == "overlap":
                self.add("broken_outline", "Building outline broken (roof triangles cross or face down)", pt,
                         "The roof of this building is drawn with overlapping or upside-down triangles (%.2f times its outline's "
                         "area, %d of %d faces upside down): the sign of a self-crossing footprint." % (ov, down, n),
                         "A footprint that crosses itself (or an inner ring treated as outer) triangulated by the builder.",
                         view=(np.array(pt) + np.array([30, 30, 30]), np.array(pt), 50.0))
            else:
                self.add("jagged_outline", "Building outline jagged or gear-shaped", pt,
                         "The roof outline zig-zags: its perimeter is %.1f times a square's of the same area." % jag,
                         "Footprint points snapped or merged badly (OSM building parts, or outline simplification).",
                         view=(np.array(pt) + np.array([30, 30, 30]), np.array(pt), 50.0))

    # 9. Made-up detail ------------------------------------------------------------------------------
    def check_generic(self):
        D = self.D
        proc = [s for s in D.surf if "buildingsnear" in s["node"].lower() or s.get("meta", {}).get("facade") == "facade_detail"
                or "facade_detail" in json.dumps(s.get("meta", {}))]
        if proc:
            n = sum(s["icount"] // 3 for s in proc)
            self.add("generic_facades", "Made-up windows on the surrounding buildings", [0, 0, 0],
                     "The buildings near the ground are drawn by the game's own facade generator (%d triangles in %s): "
                     "regular window bands on every wall, not each building's real windows, cladding or colour." % (
                         n, ", ".join(sorted(set(s["node"] for s in proc)))),
                     "GroundModels._facade: one rule for every building (floors every 3.3 m, a window band each).",
                     severity="look")
        for m in self.D.mms:
            nm = m["node"].split("/")[-1]
            if nm.startswith("Trees_") or nm.startswith("TreesFar"):
                pass
        tree_mm = [m for m in self.D.mms if m["node"].split("/")[-1].startswith("Trees")]
        if tree_mm:
            self.add("generic_trees", "Trees drawn from one stock shape", [0, 0, 0],
                     "%d trees round the ground use the game's two-lobe stock crown (%s), sized from the map; pines are a "
                     "stretched column. Same shape for every species." % (
                         sum(m["count"] for m in tree_mm), "GroundModels._canopy_mesh"),
                     "Stock tree mesh, not the real species.", severity="look")

    # 10. Anything of the model standing on the arena -----------------------------------------------
    def check_inside_fence(self):
        xs = np.arange(-self.fx, self.fx, 2.0)
        zs = np.arange(-self.fz, self.fz, 2.0)
        X, Z = np.meshgrid(xs, zs)
        X, Z = X.ravel(), Z.ravel()
        ins = (X / self.fx) ** 2 + (Z / self.fz) ** 2 < 0.97
        O = np.c_[X[ins], np.full(ins.sum(), 60.0), Z[ins]]
        idx, loc, dist = self.first(O, np.tile([0, -1, 0], (len(O), 1)))
        src = self.src(idx)
        bad = []
        for i in range(len(O)):
            if idx[i] < 0:
                continue
            if loc[i, 1] > 0.4 and (src[i] < 0 or self.D.cat[src[i]] != "oval"):
                if loc[i, 1] < 40:  # a roof over the arena is not on the arena
                    bad.append(i)
        self._cluster_report(loc[bad], "on_arena", "Something standing on the playing arena",
                             "2 m grid points inside the fence where the model, a seat leg or a surround stands 40 cm or more above the turf",
                             "Model part or seat/leg file inside the boundary.", min_n=1, cell=4.0, bowl=False,
                             view_fn=lambda p: self.close_view(p, None, 20.0))

    # ---- cameras ----------------------------------------------------------------------------------
    def make_views(self):
        D = self.D
        hl, hw = D.g["half_len"], D.g["half_wid"]
        views = []
        # broadcast (Oval3DBroadcast: main camera 15 m up, 25 m back from the wing)
        eye = np.array([0.0, 15.0, hw + 25.0])
        L, Wd = hl, hw
        views += [view_line("bc_main_far_wing", eye, [0, 1, -Wd], 45),
                  view_line("bc_main_wide", eye, [0, 1, -Wd * 0.3], 75),
                  view_line("bc_main_left_pocket", eye, [-L + 10, 1, -Wd * 0.6], 45),
                  view_line("bc_main_right_pocket", eye, [L - 10, 1, -Wd * 0.6], 45),
                  view_line("bc_goals_left", [L + 25, 15, 0], [-L, 3.3, 0], 40),
                  view_line("bc_goals_right", [-(L + 25), 15, 0], [L, 3.3, 0], 40)]
        # the model's size
        mod = np.nonzero(D.cat == "model")[0]
        mc = self.cen[mod]
        mc = mc[np.hypot(mc[:, 0], mc[:, 2]) < 400]
        R = float(np.percentile(np.hypot(mc[:, 0], mc[:, 2]), 99)) if len(mc) else 150.0
        Hm = float(np.percentile(mc[:, 1], 99.5)) if len(mc) else 30.0
        self.stats["model_radius"] = round(R, 1)
        self.stats["model_height"] = round(Hm, 1)
        # aerial orbit, 12 round
        for k in range(12):
            a = math.radians(k * 30)
            e = np.array([math.cos(a) * R * 2.1, R * 1.0, math.sin(a) * R * 2.1])
            views.append(view_line("orbit_%03d" % (k * 30), e, [0, Hm * 0.3, 0], 50))
        # street level round the outside: the outer wall by a level ray, 40 m back, eye 1.7 m over the land
        for k in range(16):
            a = math.radians(k * 22.5)
            d = np.array([math.cos(a), 0, math.sin(a)])
            o = np.array([0, 8.0, 0])
            hi_ids, ray_ids, locs = self.ray.intersects_id(np.array([o + d * 60]), np.array([d]), multiple_hits=True, return_locations=True)
            far = max([np.linalg.norm(l - o) for l, s in zip(locs, self.src(hi_ids)) if s >= 0 and D.cat[s] == "model"] or [R])
            far = min(far, R * 1.3)
            p = d * (far + 40)
            ii, ll, dd = self.first([[p[0], 250, p[2]]], [[0, -1, 0]])
            y = ll[0, 1] if np.isfinite(ll[0, 1]) else 0.0
            e = np.array([p[0], y + 1.7, p[2]])
            views.append(view_line("street_%03d" % round(k * 22.5), e, [d[0] * far * 0.8, Hm * 0.45, d[2] * far * 0.8], 70))
            if k % 2 == 0:
                e2 = np.array([p[0] * 1.6, y + 35, p[2] * 1.6])
                views.append(view_line("entrance_%03d" % round(k * 22.5), e2, [d[0] * far * 0.7, Hm * 0.35, d[2] * far * 0.7], 55))
        # seat level: 8 seats round, eye 1.2 m over the seat, looking at the field and up at the roof
        P = getattr(self, "seats_p", None)
        if P is not None and len(P):
            bear = np.degrees(np.arctan2(P[:, 2], P[:, 0])) % 360
            for k in range(8):
                sel = np.nonzero((bear >= k * 45) & (bear < k * 45 + 10))[0]
                if len(sel) == 0:
                    continue
                for tier, q in (("low", 15), ("high", 90)):
                    s = P[sel[np.argsort(P[sel, 1])[min(len(sel) - 1, len(sel) * q // 100)]]]
                    e = s + [0, 1.2, 0]
                    views.append(view_line("seat_%03d_%s" % (k * 45, tier), e, [0, 0, 0], 70))
                    up = e + np.array([s[0] * 0.15, 12, s[2] * 0.15])
                    views.append(view_line("seat_%03d_%s_up" % (k * 45, tier), e, up, 80))
        # straight down, 160 m x 90 m tiles over 960 m x 900 m
        for i in range(-3, 3):
            for j in range(-5, 5):
                cx, cz = 80 + 160 * i, 45 + 90 * j
                views.append("top_%+d_%+d %.1f 400.0 %.1f 0.0 -90.0 ortho 90" % (i, j, cx, cz))
        self.views = views + self.views


def main():
    dump_dir, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    D = Dump(dump_dir)
    osm = None
    op = os.path.join(dump_dir, "osm.json")
    if os.path.exists(op):
        osm = json.load(open(op))
    S = Scan(D, osm, out)
    S.run()
    tops = Counter()
    for s, n in zip(D.surf, np.bincount(D.sid, minlength=len(D.surf))):
        tops[(s["cat"], top_name(s["node"]))] += int(n)
    S.stats["parts"] = [[c, t, n] for (c, t), n in tops.most_common(60)]
    json.dump({"slug": D.g["slug"], "ground": D.g["ground"], "stats": S.stats, "findings": S.findings},
              open(os.path.join(out, "findings.json"), "w"), indent=1, default=float)
    open(os.path.join(out, "views.txt"), "w").write("\n".join(S.views) + "\n")
    log("wrote %d findings, %d views" % (len(S.findings), len(S.views)))


if __name__ == "__main__":
    main()
