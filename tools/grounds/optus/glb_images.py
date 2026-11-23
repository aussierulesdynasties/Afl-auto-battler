"""Swap named images inside a .glb and write it back, every other byte kept (Optus rebuild).

    from glb_images import read_glb, replace_images
    replace_images("assets/grounds/optus/optus.glb", {"bronze": png_bytes, ...})

Also `dump(path, outdir)` writes every image out as <name>.png.
"""
import json
import os
import struct


def read_glb(path):
    with open(path, "rb") as f:
        data = f.read()
    magic, version, _length = struct.unpack_from("<III", data, 0)
    assert magic == 0x46546C67 and version == 2, "not a glTF 2 binary"
    off = 12
    js, bn = None, b""
    while off < len(data):
        clen, ctype = struct.unpack_from("<II", data, off)
        chunk = data[off + 8: off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(chunk.decode("utf-8"))
        elif ctype == 0x004E4942:
            bn = chunk
        off += 8 + clen
    return js, bn


def write_glb(path, js, bn):
    jb = json.dumps(js, separators=(",", ":")).encode("utf-8")
    jb += b" " * (-len(jb) % 4)
    bn += b"\0" * (-len(bn) % 4)
    total = 12 + 8 + len(jb) + 8 + len(bn)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(jb), 0x4E4F534A))
        f.write(jb)
        f.write(struct.pack("<II", len(bn), 0x004E4942))
        f.write(bn)


def _view_bytes(js, bn, i):
    bv = js["bufferViews"][i]
    o = bv.get("byteOffset", 0)
    return bn[o: o + bv["byteLength"]]


def replace_images(path, new, mime="image/png", out=None):
    """`new` maps an image name to its encoded bytes. Rebuilds the binary chunk view by view."""
    js, bn = read_glb(path)
    by_view = {}
    for im in js["images"]:
        if im.get("name") in new:
            by_view[im["bufferView"]] = new[im["name"]]
            im["mimeType"] = mime
    missing = set(new) - {im.get("name") for im in js["images"]}
    assert not missing, "no image named %s" % sorted(missing)
    out_bin = bytearray()
    for i, bv in enumerate(js["bufferViews"]):
        chunk = by_view.get(i, _view_bytes(js, bn, i))
        out_bin += b"\0" * (-len(out_bin) % 4)
        bv["byteOffset"] = len(out_bin)
        bv["byteLength"] = len(chunk)
        out_bin += chunk
    js["buffers"][0]["byteLength"] = len(out_bin)
    write_glb(out or path, js, bytes(out_bin))


def dump(path, outdir):
    js, bn = read_glb(path)
    os.makedirs(outdir, exist_ok=True)
    for im in js["images"]:
        with open(os.path.join(outdir, im["name"] + ".png"), "wb") as f:
            f.write(_view_bytes(js, bn, im["bufferView"]))
