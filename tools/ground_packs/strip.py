"""Keep only one ground's own files from an exported pack.

Godot always puts the project's own files in an exported pack (project.binary, the autoload
scripts, the icons, the uid and class caches). A ground's pack must hold nothing but that
ground, or loading it could stand an older copy of the game's own files over the build's.
This copies the entries under res://assets/grounds/<slug>/ and res://.godot/imported/ out of
<exported.pck> into <dir>, as files at their res:// paths, for pack.gd to pack again.

    python3 strip.py <exported.pck> <slug> <dir>
"""
import os
import struct
import sys


def entries(path):
    with open(path, "rb") as f:
        if f.read(4) != b"GDPC":
            raise SystemExit("not a Godot pack: " + path)
        fmt, _ma, _mi, _pa, flags = struct.unpack("<5I", f.read(20))
        if flags & 1:
            raise SystemExit("encrypted pack directory: " + path)
        base = struct.unpack("<Q", f.read(8))[0]
        if fmt >= 3:
            f.seek(struct.unpack("<Q", f.read(8))[0])
        else:
            f.read(64)
        out = []
        for _ in range(struct.unpack("<I", f.read(4))[0]):
            n = struct.unpack("<I", f.read(4))[0]
            name = f.read(n).rstrip(b"\0").decode()
            off, size = struct.unpack("<QQ", f.read(16))
            f.read(16)
            eflags = struct.unpack("<I", f.read(4))[0]
            if eflags & 1:
                raise SystemExit("encrypted file in pack: " + name)
            out.append((name, base + off, size))
        return out


def main():
    pck, slug, dest = sys.argv[1], sys.argv[2], sys.argv[3]
    keep = ("assets/grounds/%s/" % slug, ".godot/imported/")
    kept = 0
    with open(pck, "rb") as f:
        for name, off, size in entries(pck):
            rel = name[len("res://"):] if name.startswith("res://") else name
            if not rel.startswith(keep):
                continue
            target = os.path.join(dest, rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            f.seek(off)
            with open(target, "wb") as o:
                o.write(f.read(size))
            kept += 1
    print(kept)


if __name__ == "__main__":
    main()
