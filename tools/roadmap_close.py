"""Keep docs/TODO.md in step with what merges: close finished rows, note progress.

PRs never edit docs/TODO.md themselves (parallel PRs conflicted there). The PR body
names its row on a line of its own:
  "Closes row 54" / "Closes rows 22, 27" / "Closes row T5.Q24": the row is deleted;
  "Part of row 142" / "Part of rows 131, 132": docs/TODO_MERGED.md gains "- 142: Merged #N: title."
  (once per row and PR; the row itself is untouched, so TODO.md stays under its 60 KB budget);
  "No row: <why>": the PR is outside the list (CI, a hotfix of a closed row).
The roadmap_close workflow runs this after the merge, and the Tests plan job runs
--check on every pull request, so a PR that names no row (or a row that does not
exist) fails before it can merge (director 2026-11-14: the list fell 25 PRs behind).
A row matches when its first table cell equals the id exactly. Only matching lines
change; the BOM, line endings and every other byte stay as they were. Stdlib only.

    python3 tools/roadmap_close.py --body-file body.txt [--todo docs/TODO.md] [--dry-run]
        [--pr N --title "PR title"] [--log docs/TODO_MERGED.md]
    python3 tools/roadmap_close.py --check --body-file body.txt [--todo docs/TODO.md]
Prints the changed ids (comma-separated) on stdout; warnings go to stderr.
"""
import argparse
import pathlib
import re
import sys

CLOSES = re.compile(r"(?im)^[\s>*-]*closes?\s+rows?\s+(.+?)\s*$")
PART = re.compile(r"(?im)^[\s>*-]*part\s+of\s+rows?\s+(.+?)\s*$")
NO_ROW = re.compile(r"(?im)^[\s>*-]*no\s+row:\s*\S")
# A row id has a digit (54, T5.Q24, 6.44), so header cells like "Id" never match.
ID = re.compile(r"(?=[A-Za-z0-9._-]*\d)[A-Za-z0-9][A-Za-z0-9._-]*")
SEP = re.compile(r"\s*(?:,|\band\b|&)\s*|\s+")


def parse_ids(body, pattern=CLOSES):
    """Row-id groups named in a PR body: one list per matching line.

    Ids are read left to right and stop at the first word that is not an id, so
    "Closes row 54 for the ruck" names only 54 and "Closes row 25 (see 12)" only 25."""
    groups = []
    for m in pattern.finditer(body or ""):
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


def _is_row(cell, want):
    return cell is not None and cell in want and not set(cell) <= set("-: ")


def close_rows(text, ids):
    """Return (new_text, closed_ids). text is the decoded file, BOM included."""
    want = set(ids)
    out, closed = [], []
    for line in text.splitlines(keepends=True):
        cell = first_cell(line)
        if _is_row(cell, want):
            if cell not in closed:
                closed.append(cell)
            continue
        out.append(line)
    return "".join(out), closed


LOG_HEAD = ("# Merged toward open rows\n\n"
            "What has landed toward each open row of docs/TODO.md and docs/TODO_RULINGS.md, one line per "
            "merged PR, oldest first. tools/roadmap_close.py writes it from a PR's \"Part of row N\" line "
            "after the merge. A reference, not a must-read: read a row's lines when you pick that row up.\n\n")


def note_log(log, ids, pr, title):
    """Return (new_log, noted_ids): each row named gains a line "- id: Merged #pr: title."
    in the merge log. A row that already has #pr's line is left alone, so a rebuild of an
    old notes PR finds nothing to change. The rows themselves never grow (TODO.md has a
    60 KB budget, tools/check_doc_sizes.py)."""
    log = log or LOG_HEAD
    if not log.endswith("\n"):
        log += "\n"
    noted = []
    for i in ids:
        if i in noted or re.search(rf"(?m)^- {re.escape(i)}: Merged #{re.escape(str(pr))}:", log):
            continue
        log += f"- {i}: Merged #{pr}: {title.strip().rstrip('.')}.\n"
        noted.append(i)
    return log, noted


def check(body, text):
    """None when the PR body names its place in the list, else the error to show."""
    named = resolve(text, parse_ids(body)) + resolve(text, parse_ids(body, PART))
    if not named:
        if NO_ROW.search(body or ""):
            return None
        return ("The PR body names no docs/TODO.md row. Add a line of its own: 'Closes row N' "
                "(finished), 'Part of row N' (progress: the row notes the merge) or "
                "'No row: <why>'. Then re-run the failed jobs.")
    cells = {first_cell(l) for l in text.splitlines()}
    missing = [i for i in named if i not in cells]
    if missing:
        return (f"No docs/TODO.md or TODO_RULINGS.md row has the id {', '.join(missing)}. "
                "Name an existing row, or write 'No row: <why>'.")
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--body-file", required=True)
    ap.add_argument("--todo", action="append",
                    help="a list file to read; repeat it for several (default docs/TODO.md)")
    ap.add_argument("--log", default="",
                    help="the merge log for 'Part of row N' (default TODO_MERGED.md beside the first --todo)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true", help="fail when the body names no row")
    ap.add_argument("--pr", default="")
    ap.add_argument("--title", default="")
    a = ap.parse_args(argv)
    body = pathlib.Path(a.body_file).read_text(encoding="utf-8", errors="replace")
    paths = [pathlib.Path(t) for t in (a.todo or ["docs/TODO.md"])]
    texts = [p.read_bytes().decode("utf-8") for p in paths]  # keeps a leading BOM as U+FEFF
    if a.check:
        err = check(body, "\n".join(texts))
        if err:
            print(err, file=sys.stderr)
            return 1
        return 0
    ids, parts = parse_ids(body), parse_ids(body, PART)
    if not ids and not parts:
        print("warning: PR body names no 'Closes row N' or 'Part of row N'; nothing to do", file=sys.stderr)
        return 0
    closed, keep = [], []
    for path, text in zip(paths, texts):
        new, shut = close_rows(text, resolve(text, ids))
        if parts and a.pr:
            cells = {first_cell(l) for l in new.splitlines()}
            keep += [i for i in resolve(new, parts) if i in cells and i not in shut and i not in keep]
        closed += [i for i in shut if i not in closed]
        if new != text and not a.dry_run:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(new)
    noted = []
    if keep:
        log_path = pathlib.Path(a.log) if a.log else paths[0].with_name("TODO_MERGED.md")
        log = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
        new_log, noted = note_log(log, keep, a.pr, a.title)
        if new_log != log and not a.dry_run:
            with open(log_path, "w", encoding="utf-8", newline="") as f:
                f.write(new_log)
    changed = closed + noted
    if not changed:
        print(f"warning: no TODO row matches {'; '.join(', '.join(g) for g in ids + parts)}", file=sys.stderr)
        return 0
    if closed:
        print(f"closing: {', '.join(closed)}", file=sys.stderr)
    if noted:
        print(f"noting the merge on: {', '.join(noted)}", file=sys.stderr)
    print(", ".join(changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
