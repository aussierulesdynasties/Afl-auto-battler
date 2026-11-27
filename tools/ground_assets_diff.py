"""Print the ground files whose pinned version differs between two commits (docs/GROUND_ASSETS.md).

The ground models live in a private repo; this repo holds only their pin, tools/ground_assets.lock
(a sha256 per path). `git diff --name-only` shows a rebuilt model as one changed lock file, so the
checks that ask "which grounds changed?" (ground-shots.yml) add this script's paths to that list.

  python3 tools/ground_assets_diff.py BASE HEAD    # one assets/grounds/... path per line
"""
import subprocess
import sys

LOCK = "tools/ground_assets.lock"


def pins(ref):
    try:
        text = subprocess.run(["git", "show", f"{ref}:{LOCK}"], capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return {}
    out = {}
    for line in text.splitlines():
        sha, sep, path = line.partition("  ")
        if sep and len(sha) == 64:
            out[path] = sha
    return out


def main():
    base, head = pins(sys.argv[1]), pins(sys.argv[2])
    for path in sorted(set(base) | set(head)):
        if base.get(path) != head.get(path):
            print(path)


if __name__ == "__main__":
    main()
