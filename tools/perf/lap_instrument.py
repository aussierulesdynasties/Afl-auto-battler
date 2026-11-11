#!/usr/bin/env python3
"""Put perf_lap.gd step timers into a throwaway bench tree (T8.Q20).

  python3 tools/perf/lap_instrument.py <tree> <targets file>

Each target line is "path/File.gd func_name". A function missing from the
tree is skipped (older trees). Every top-level statement of the function body
(one tab deep, outside open brackets) gets a lap() before it, labelled with its
line number and text. Never run on a working checkout: it rewrites files.
"""
import re
import sys
from pathlib import Path


def scan_depth(line, depth):
    """Bracket depth after this line, ignoring strings and comments."""
    i, n, q = 0, len(line), None
    while i < n:
        c = line[i]
        if q:
            if c == "\\":
                i += 2
                continue
            if line.startswith(q, i):
                i += len(q)
                q = None
                continue
        else:
            if c == "#":
                break
            if line.startswith('"""', i):
                q = '"""'
                i += 3
                continue
            if c in "\"'":
                q = c
            elif c in "([{":
                depth += 1
            elif c in ")]}":
                depth -= 1
        i += 1
    return depth


def instrument(lines, fn, cls):
    head = re.compile(r"^(static\s+)?func\s+" + re.escape(fn) + r"\s*\(")
    start = next((i for i, l in enumerate(lines) if head.match(l)), None)
    if start is None:
        return lines, 0
    # The signature ends at the first line whose depth returns to 0.
    depth, i = 0, start
    while True:
        depth = scan_depth(lines[i], depth)
        if depth <= 0 and lines[i].rstrip().endswith(":"):
            break
        i += 1
    body = i + 1
    end = body
    while end < len(lines) and (not lines[end].strip() or lines[end].startswith("	") or lines[end].startswith("#")):
        end += 1
    # trim trailing blank / column-0 comment lines
    while end > body and (lines[end - 1].strip() == "" or not lines[end - 1].startswith("\t")):
        end -= 1
    out = lines[:body]
    out.append('\tvar __pl = preload("res://tools/perf/perf_lap.gd").new("%s.%s")\n' % (cls, fn))
    depth, cont, count = 0, False, 0
    for k in range(body, end):
        l = lines[k]
        s = l.strip()
        top = (depth == 0 and not cont and l.startswith("\t") and not l.startswith("\t\t")
               and s and not s.startswith("#") and not re.match(r"(elif|else)\b", s))
        if top:
            label = re.sub(r"\s+", " ", s)[:70].replace("\\", "/").replace('"', "'")
            out.append('\t__pl.lap("L%d %s")\n' % (k + 1, label))
            count += 1
        out.append(l)
        if s and not s.startswith("#"):
            depth = scan_depth(l, depth)
            cont = l.rstrip().endswith("\\")
    out.extend(lines[end:])
    return out, count


def main():
    tree, targets = Path(sys.argv[1]), Path(sys.argv[2])
    by_file = {}
    for t in targets.read_text().splitlines():
        t = t.split("#", 1)[0].strip()
        if t:
            f, fn = t.split()
            by_file.setdefault(f, []).append(fn)
    for f, fns in by_file.items():
        p = tree / f
        if not p.exists():
            print("LAPS skip %s (missing)" % f)
            continue
        lines = p.open(encoding="utf-8", newline="").read().splitlines(keepends=True)
        cls = p.stem
        # Last function first, so each label keeps the line number of the real file.
        def at(fn):
            m = re.compile(r"^(static\s+)?func\s+" + re.escape(fn) + r"\s*\(")
            return next((i for i, l in enumerate(lines) if m.match(l)), -1)
        for fn in sorted(fns, key=at, reverse=True):
            lines, n = instrument(lines, fn, cls)
            print("LAPS %s.%s: %s" % (cls, fn, ("%d statements" % n) if n else "not in this tree"))
        p.open("w", encoding="utf-8", newline="").write("".join(lines))


if __name__ == "__main__":
    main()
