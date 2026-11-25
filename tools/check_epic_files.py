"""Fails if an Epic/MetaHuman file is committed to this public repo (docs/EPIC_ASSETS.md).

    python3 -I tools/check_epic_files.py          # every tracked file (CI lint job)
    python3 -I tools/check_epic_files.py --commits BASE..HEAD
                                                  # also no commit in the range holds one (after the
                                                  # history purge, docs/EPIC_ASSETS.md)

The Unreal Engine EULA lets MetaHuman files leave our hands only inside a built game, so they
live in a private repo and tools/epic_assets.sh copies them in. This check fails when:

1. a file pinned in tools/epic_assets.lock is tracked here;
2. a tracked file sits where only Epic-derived files go (assets/oval3d/cuts/, assets/oval3d/skin/);
3. a tracked model or texture's name says MetaHuman (metahuman, an "mh" name part such as
   player_mh.glb or MH_Head), or it is an Unreal .uasset/.umap, a MetaHuman .dna or a .groom;
4. a tracked .glb/.gltf names a mesh, node, material, image or skin after a MetaHuman part;
5. a tracked file is byte for byte a version of an Epic file this repo once held, under any
   name (tools/epic_blobs.txt lists their git blob ids);
6. a tracked model or texture under assets/oval3d/ is not declared in tools/epic_guard_allow.txt
   with where it came from (so a new body part is a deliberate, sourced decision).
"""
import json
import re
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK = ROOT / "tools" / "epic_assets.lock"
ALLOW = ROOT / "tools" / "epic_guard_allow.txt"
BLOBS = ROOT / "tools" / "epic_blobs.txt"

EPIC_ONLY_DIRS = ("assets/oval3d/cuts/", "assets/oval3d/skin/")
EPIC_EXT = {".uasset", ".umap", ".dna", ".groom", ".abc_groom"}
# "mh" as its own word part (player_mh.glb, MH_Head, mh_grooms), never inside a word (gmhba).
NAME_RE = re.compile(r"(?i)metahuman|(^|[^a-z0-9])mh([^a-z0-9]|$)")
# Names MetaHuman exports carry inside a model file.
GLB_NAME_RE = re.compile(r"(?i)metahuman|(^|[^a-z0-9])mh([^a-z0-9]|$)|fullbody|facemesh|groom")
DECLARE_EXT = {".glb", ".gltf", ".res", ".tres", ".scn", ".mesh", ".obj", ".fbx",
               ".png", ".jpg", ".jpeg", ".webp", ".exr", ".ktx", ".ktx2", ".bin"}
DECLARE_DIR = "assets/oval3d/"


def tracked() -> dict[str, str]:
    """path -> git blob id of every tracked file."""
    out = subprocess.run(["git", "ls-files", "-s", "-z"], cwd=ROOT, capture_output=True, check=True)
    files = {}
    for rec in out.stdout.decode("utf-8").split("\0"):
        if rec:
            meta, path = rec.split("\t", 1)
            files[path] = meta.split()[1]
    return files


def epic_blobs() -> set[str]:
    if not BLOBS.exists():
        return set()
    return {m.group(1) for m in re.finditer(r"^([0-9a-f]{40})\b", BLOBS.read_text(), re.M)}


def pinned() -> set[str]:
    if not LOCK.exists():
        return set()
    return {m.group(1) for m in re.finditer(r"^[0-9a-f]{64}  (.+)$", LOCK.read_text(), re.M)}


def allowed() -> set[str]:
    if not ALLOW.exists():
        return set()
    keep = set()
    for line in ALLOW.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            keep.add(line.split()[0])
    return keep


def glb_names(path: Path) -> list[str]:
    """Every name in a glTF's JSON (the GLB's first chunk only: cheap even for big files)."""
    try:
        with path.open("rb") as f:
            head = f.read(20)
            if path.suffix == ".gltf":
                doc = json.loads(head + f.read())
            else:
                if len(head) < 20 or head[:4] != b"glTF":
                    return []
                length = struct.unpack("<I", head[12:16])[0]
                doc = json.loads(f.read(length))
    except (OSError, ValueError):
        return []
    names = []
    for key in ("meshes", "nodes", "materials", "images", "skins", "textures"):
        for item in doc.get(key, []):
            for field in ("name", "uri"):
                if isinstance(item.get(field), str):
                    names.append(item[field])
    return names


def history_faults(rng: str, blobs: set[str]) -> list[str]:
    """Commits in rng that carry an Epic blob anywhere in their trees."""
    out = subprocess.run(["git", "rev-list", "--objects", rng], cwd=ROOT, capture_output=True,
                         text=True, check=True)
    hits = {}
    for line in out.stdout.splitlines():
        oid, _, path = line.partition(" ")
        if oid in blobs:
            hits[oid] = path
    return [f"history {rng}: {path} ({oid[:10]}) is in a commit; rebuild the branch from the purged main"
            for oid, path in sorted(hits.items(), key=lambda kv: kv[1])]


def main() -> int:
    files = tracked()
    lock, allow, blobs = pinned(), allowed(), epic_blobs()
    faults = []
    for p, blob in files.items():
        if not (ROOT / p).is_file():
            continue  # deleted in the working tree
        low = p.lower()
        name = p.rsplit("/", 1)[-1]
        ext = ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else ""
        if ext in {".import", ".uid"}:
            continue  # Godot's import settings: no content of the file itself
        if blob in blobs:
            faults.append(f"{p}: is a copy of an Epic/MetaHuman file (tools/epic_blobs.txt)")
        elif p in lock:
            faults.append(f"{p}: pinned in tools/epic_assets.lock (private repo), must not be committed")
        elif low.startswith(EPIC_ONLY_DIRS):
            faults.append(f"{p}: only Epic-derived files live here; publish it with tools/epic_assets.sh")
        elif ext in EPIC_EXT or (ext in DECLARE_EXT and p not in allow
                                 and NAME_RE.search(name.rsplit(".", 1)[0])):
            faults.append(f"{p}: the name says MetaHuman/Unreal")
        elif ext in {".glb", ".gltf"}:
            hits = sorted({n for n in glb_names(ROOT / p) if GLB_NAME_RE.search(n)})
            if hits:
                faults.append(f"{p}: names MetaHuman parts inside ({', '.join(hits[:4])})")
        if (low.startswith(DECLARE_DIR) and ext in DECLARE_EXT and p not in allow
                and not low.startswith(EPIC_ONLY_DIRS) and p not in lock):
            faults.append(f"{p}: a model or texture under assets/oval3d/ that tools/epic_guard_allow.txt "
                          "does not declare (add it with its source if it is not Epic's)")
    if "--commits" in sys.argv:
        faults += history_faults(sys.argv[sys.argv.index("--commits") + 1], blobs)
    if faults:
        print("Epic/MetaHuman files must not be committed to this public repo (docs/EPIC_ASSETS.md):")
        for f in faults:
            print("  " + f)
        print("Move them to the private repo: tools/epic_assets.sh publish \"why\" PATH...")
        return 1
    print(f"No Epic/MetaHuman files tracked ({len(files)} files checked, {len(lock)} kept private).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
