"""Delete the docs/TODO.md table rows a merged PR names with "Closes row N".

PRs never edit docs/TODO.md themselves (parallel PRs conflicted there). The PR body
carries lines like "Closes row 54", "Closes rows 22, 27" or "Closes row T5.Q24";
the roadmap_close workflow runs this after the merge. A row matches when its first
table cell equals the id exactly. Only matching lines are removed; the BOM, line
endings and every other byte stay as they were. Stdlib only.

    python3 tools/roadmap_close.py --body-file body.txt [--todo docs/TODO.md] [--dry-run]
Prints the closed ids (comma-separated) on stdout; warnings go to stderr.
"""
import argparse
import pathlib
import re
import sys

CLOSES = re.compile(r"(?im)^[\s>*-]*closes?\s+rows?\s+(.+?)\s*$")
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def parse_ids(body):
    """Row ids named in a PR body, in order, without duplicates.

    "Closes rows 35, 36" also yields "35, 36", so a row whose first cell is
    literally "35, 36" can be closed too."""
    ids = []
    for m in CLOSES.finditer(body or ""):
        spec = m.group(1).strip().rstrip(".")
        parts = ID.findall(re.sub(r"\band\b", ",", spec))
        cands = parts + ([", ".join(parts)] if len(parts) > 1 else [])
        for c in cands:
            if c not in ids:
                ids.append(c)
    return ids


def first_cell(line):
    s = line.strip()
    if not s.startswith("|"):
        return None
    cells = s.split("|")
    return cells[1].strip() if len(cells) > 2 else None


def close_rows(text, ids):
    """Return (new_text, closed_ids). text is the decoded file, BOM included."""
    want = set(ids)
    out, closed = [], []
    for line in text.splitlines(keepends=True):
        cell = first_cell(line)
        if cell is not None and cell in want and not set(cell) <= set("-: "):
            if cell not in closed:
                closed.append(cell)
            continue
        out.append(line)
    return "".join(out), closed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--body-file", required=True)
    ap.add_argument("--todo", default="docs/TODO.md")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    body = pathlib.Path(a.body_file).read_text(encoding="utf-8", errors="replace")
    ids = parse_ids(body)
    if not ids:
        print("warning: PR body names no 'Closes row N'; nothing to close", file=sys.stderr)
        return 0
    path = pathlib.Path(a.todo)
    raw = path.read_bytes()
    text = raw.decode("utf-8")  # keeps a leading BOM as U+FEFF
    new, closed = close_rows(text, ids)
    if not closed:
        print(f"warning: no TODO row matches {', '.join(ids)}", file=sys.stderr)
        return 0
    print(f"closing: {', '.join(closed)}", file=sys.stderr)
    if not a.dry_run:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new)
    print(", ".join(closed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
