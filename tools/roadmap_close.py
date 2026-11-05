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
# A row id has a digit (54, T5.Q24, 6.44), so header cells like "Id" never match.
ID = re.compile(r"(?=[A-Za-z0-9._-]*\d)[A-Za-z0-9][A-Za-z0-9._-]*")
SEP = re.compile(r"\s*(?:,|\band\b|&)\s*|\s+")


def parse_ids(body):
    """Row-id groups named in a PR body: one list per "Closes row" line.

    Ids are read left to right and stop at the first word that is not an id, so
    "Closes row 54 for the ruck" names only 54 and "Closes row 25 (see 12)" only 25."""
    groups = []
    for m in CLOSES.finditer(body or ""):
        spec = m.group(1).strip()
        ids, pos = [], 0
        while pos < len(spec):
            t = ID.match(spec, pos)
            if not t:
                break
            ids.append(t.group().rstrip("."))
            pos = t.end()
            sep = SEP.match(spec, pos)
            if not sep or not sep.group():
                break
            pos = sep.end()
        ids = [i for i in ids if i]
        if ids:
            groups.append(ids)
    return groups


def resolve(text, groups):
    """Flatten groups to row ids. A multi-id group whose joined form ("35, 36") is
    itself a row's first cell closes only that combined row, not the single rows."""
    cells = {first_cell(l) for l in text.splitlines()}
    out = []
    for g in groups:
        joined = ", ".join(g)
        for c in ([joined] if len(g) > 1 and joined in cells else g):
            if c not in out:
                out.append(c)
    return out


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
    new, closed = close_rows(text, resolve(text, ids))
    if not closed:
        print(f"warning: no TODO row matches {'; '.join(', '.join(g) for g in ids)}", file=sys.stderr)
        return 0
    print(f"closing: {', '.join(closed)}", file=sys.stderr)
    if not a.dry_run:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new)
    print(", ".join(closed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
