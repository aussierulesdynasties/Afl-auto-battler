"""gdlint (gdtoolkit, pinned in tools/lint/requirements.txt) over the GDScript, against a baseline.

The config is tools/lint/gdlintrc: naming rules, unused arguments, whitespace and tab guards;
layout and size rules are off. gdtoolkit's parser lags Godot 4.7 on a few legal forms, and a
file it cannot parse is not linted at all, so a parse error is never baselined: it always fails,
naming the rewrite that parses (PARSE_HINT). Every tracked .gd parsed on 2026-11-12.

tools/lint/gdlint_baseline.txt holds today's known problems as "count rule path". A file may
have up to its baseline count of each rule; one more fails, naming each line of that rule in
that file. Fix a baselined problem and the gate says the baseline can shrink (never a failure);
rewrite it with `python3 -I tools/lint/lint.py --only gdlint --write-baseline`.
"""
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

from common import Finding

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(HERE, "gdlint_baseline.txt")
VERSION = "4.5.0"
PROBLEM = re.compile(r"^(.+?\.gd):(\d+): Error: (.*) \(([\w-]+)\)\s*$")
PARSE_HEAD = re.compile(r"^(.+?\.gd):\s*$")
AT_LINE = re.compile(r"\bline (\d+)")
PARSE_HINT = ("gdtoolkit cannot parse this file, so gdlint checks none of it. Forms Godot accepts but "
              "gdtoolkit 4.5.0 does not: a line break inside a \"...\" string (write \\n), `set` or `get` "
              "as a variable name (rename it), `x == not y` (write `x == (not y)`), a one-line lambda "
              "with an `if` body (put the body on its own lines)")


def available():
    """gdtoolkit's version string, or None when it is not installed."""
    try:
        r = subprocess.run([sys.executable, "-m", "gdtoolkit.linter", "--version"], capture_output=True, text=True, cwd=HERE)
    except OSError:
        return None
    return r.stdout.strip().split()[-1] if r.returncode == 0 and r.stdout.strip() else None


def _rel(root, path):
    p = path.replace("\\", "/")
    prefix = os.path.relpath(root, HERE).replace("\\", "/") + "/"
    return p[len(prefix):] if p.startswith(prefix) else p


def parse(root, text):
    """gdlint's output as findings (a file that does not parse is one "parse-error")."""
    out = []
    pending = None  # (path, [lines]) of a parse error being read
    for line in text.split("\n"):
        m = PROBLEM.match(line)
        h = PARSE_HEAD.match(line) if not m else None
        if (m or h) and pending:
            out.append(_parse_error(*pending))
            pending = None
        if m:
            out.append(Finding(_rel(root, m.group(1)), int(m.group(2)), m.group(4), m.group(3)))
        elif h:
            pending = (_rel(root, h.group(1)), [])
        elif pending is not None:
            pending[1].append(line)
    if pending:
        out.append(_parse_error(*pending))
    return out


def _parse_error(path, lines):
    body = "\n".join(lines)
    m = AT_LINE.search(body)
    first = next((ln.strip() for ln in lines if ln.strip()), "gdtoolkit could not parse the file")
    return Finding(path, int(m.group(1)) if m else 0, "parse-error", first[:160])


def run(root, files, jobs=None):
    """Lint the repo-relative .gd files (chunked, in parallel); every problem found."""
    rel_root = os.path.relpath(root, HERE)
    args = [os.path.join(rel_root, f).replace("\\", "/") for f in files]
    chunks = [args[i:i + 40] for i in range(0, len(args), 40)]

    def one(chunk):
        r = subprocess.run([sys.executable, "-m", "gdtoolkit.linter"] + chunk, capture_output=True, text=True, cwd=HERE)
        return r.stdout + "\n" + r.stderr

    with ThreadPoolExecutor(max_workers=jobs or os.cpu_count() or 4) as ex:
        texts = list(ex.map(one, chunks))
    found = []
    for t in texts:
        found += parse(root, t)
    return found


def read_baseline(path=BASELINE):
    base = {}
    if not os.path.exists(path):
        return base
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            n, rule, p = line.split(" ", 2)
            base[(p, rule)] = int(n)
    return base


def write_baseline(found, path=BASELINE):
    counts = {}
    for f in found:
        counts[(f.path, f.rule)] = counts.get((f.path, f.rule), 0) + 1
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# gdlint problems known on the day the gate started (tools/lint/gdlint_gate.py): count rule path.\n")
        fh.write("# Shrinks as they are fixed; never grows by hand. Rewrite: python3 -I tools/lint/lint.py --only gdlint --write-baseline\n")
        for (p, rule) in sorted(counts):
            fh.write("%d %s %s\n" % (counts[(p, rule)], rule, p))
    return counts


def gate(found, files, base=None):
    """(new problems as findings, notes) for the linted files against the baseline."""
    base = read_baseline() if base is None else base
    by = {}
    for f in found:
        by.setdefault((f.path, f.rule), []).append(f)
    out, notes = [], []
    for key in sorted(by):
        allowed = 0 if key[1] == "parse-error" else base.get(key, 0)
        if len(by[key]) > allowed:
            for f in by[key]:
                if f.rule == "parse-error":
                    out.append(Finding(f.path, f.line, "gdlint/parse-error", f.message + ". " + PARSE_HINT))
                    continue
                out.append(Finding(f.path, f.line, "gdlint/" + f.rule, f.message + (
                    "" if not allowed else " (%d of this rule in this file, baseline %d)" % (len(by[key]), allowed))))
    linted = set(files)
    for (p, rule), n in sorted(base.items()):
        if p in linted and len(by.get((p, rule), [])) < n:
            notes.append("%s: %s now %d, baseline %d: the baseline can shrink" % (p, rule, len(by.get((p, rule), [])), n))
    return out, notes
