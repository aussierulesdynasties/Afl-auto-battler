#!/usr/bin/env python3
"""The CI cache of Godot's import (.godot), so a job re-imports only what changed.

A fresh checkout imports every ground model and texture again: about 11 minutes on a
GitHub runner (preflight log, 2026-11-26: "import: 683 s"), in the preflight, every
shard and the extras job of every run. With last main's .godot restored, Godot checks
each source against the md5 it stored and re-imports only the files that differ, so a
restored cache can never hand a suite a stale import.

  python3 tools/ci_import_cache.py key     # the cache key's content part (hash of every import input)
  python3 tools/ci_import_cache.py prune   # strip .godot to what may be cached, before a save

What may be cached (docs/EPIC_ASSETS.md): the Unreal Engine EULA lets the Epic/MetaHuman
files leave our hands only inside a built game, and a public repo's cache is readable by
fork pull requests. So prune keeps only the import of a file whose .import is tracked here
and which is not an Epic file (tools/epic_assets.lock, or a folder only Epic files use).
Godot names each import <file>-<md5 of its res:// path>.*. The ground models fetched from
the private repo (tools/ground_assets.lock) are ours and may be cached. The editor's file
index and class caches are kept too: they hold paths and hashes, not content. Everything
else is deleted, and each job re-imports it.
"""
import hashlib
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GODOT_DIR = ROOT / ".godot"
# .godot entries kept besides imported/: the editor's file index (paths, times, md5s) and
# the class and uid caches. Anything else Godot writes there is left out of the cache.
KEEP = {"imported", "editor", "global_script_class_cache.cfg", "uid_cache.bin", "extension_list.cfg"}


def tracked() -> dict[str, str]:
    """path -> blob id of every tracked file (from the index, so sparse paths count too)."""
    out = subprocess.run(["git", "ls-files", "-s", "-z"], cwd=ROOT, capture_output=True, check=True)
    files = {}
    for rec in out.stdout.decode("utf-8").split("\0"):
        if rec:
            meta, path = rec.split("\t", 1)
            files[path] = meta.split()[1]
    return files


# Folders that hold only Epic-derived files (as tools/check_epic_files.py).
EPIC_ONLY_DIRS = ("assets/oval3d/cuts/", "assets/oval3d/skin/")


def epic_paths() -> set[str]:
    lock = ROOT / "tools" / "epic_assets.lock"
    if not lock.exists():
        return set()
    return {m.group(1) for m in re.finditer(r"^[0-9a-f]{64}  (.+)$", lock.read_text(), re.M)}


def key(files: dict[str, str]) -> str:
    """Hash of every import input: each tracked file that is imported, each .import, the
    asset locks (files fetched from private repos are not tracked here), and project.godot."""
    h = hashlib.sha256()
    for path in sorted(files):
        if (path.endswith(".import") or path + ".import" in files or path == "project.godot"
                or (path.startswith("tools/") and path.endswith(".lock"))):
            h.update(f"{files[path]} {path}\n".encode())
    return h.hexdigest()[:20]


def public_prefixes(files: dict[str, str]) -> set[str]:
    """The .godot/imported name prefix of every imported file that may be cached: its .import
    is tracked, and it is not an Epic file."""
    out = set()
    epic = epic_paths()
    for imp in files:
        if not imp.endswith(".import"):
            continue
        path = imp[: -len(".import")]
        if path in epic or path.startswith(EPIC_ONLY_DIRS):
            continue
        md5 = hashlib.md5(f"res://{path}".encode()).hexdigest()
        out.add(f"{path.rsplit('/', 1)[-1]}-{md5}")
    return out


def prune(files: dict[str, str]) -> int:
    if not GODOT_DIR.is_dir():
        print("No .godot to prune")
        return 1
    for entry in GODOT_DIR.iterdir():
        if entry.name not in KEEP:
            shutil.rmtree(entry) if entry.is_dir() else entry.unlink()
    keep = public_prefixes(files)
    kept = dropped = 0
    imported = GODOT_DIR / "imported"
    if imported.is_dir():
        for f in imported.iterdir():
            # "<file>-<32 hex>" then ".<ext>" (or more, as in .s3tc.ctex)
            name = f.name
            cut = name.find(".", name.rfind("-") + 1)
            if f.is_file() and cut > 0 and name[:cut] in keep:
                kept += 1
            else:
                shutil.rmtree(f) if f.is_dir() else f.unlink()
                dropped += 1
    # Belt and braces: no Epic file's import may survive, whatever the rule above says.
    epic = {f"{p.rsplit('/', 1)[-1]}-{hashlib.md5(f'res://{p}'.encode()).hexdigest()}"
            for p in epic_paths() | {i[:-len(".import")] for i in files
                                    if i.endswith(".import") and i.startswith(EPIC_ONLY_DIRS)}}
    left = [f.name for f in imported.iterdir() if any(f.name.startswith(e + ".") for e in epic)] \
        if imported.is_dir() else []
    if left:
        print(f"::error::an Epic file's import is still in .godot after the prune: {left[:3]}")
        shutil.rmtree(GODOT_DIR)
        return 1
    print(f"Import cache: kept {kept} files of tracked sources, dropped {dropped} (Epic files and files with no tracked .import)")
    return 0


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    files = tracked()
    if cmd == "key":
        print(key(files))
        return 0
    if cmd == "prune":
        return prune(files)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
