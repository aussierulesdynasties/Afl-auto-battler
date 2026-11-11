#!/usr/bin/env python3
"""Put perf_lap.gd step timers into a throwaway bench tree (T8.Q20).

  python3 tools/perf/lap_instrument.py <tree> <targets file>

Each target line is "path/File.gd func_name". A function missing from the
tree is skipped (older trees). The function is renamed <name>__lapped and every
top-level statement of its body (one tab deep, outside open brackets) gets a
lap() before it, labelled with its line number and text. A wrapper under the
old name calls it and closes the last lap. Never run on a working checkout: it
rewrites files.
"""
import re
import sys
from pathlib import Path

NL = "\n"
TAB = "\t"
PERF = 'preload("res://tools/perf/perf_lap.gd")'


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


def func_re(fn):
    return re.compile(r"^(static\s+)?func\s+" + re.escape(fn) + r"\s*\(")


def instrument(lines, fn, cls):
    head = func_re(fn)
    start = next((i for i, l in enumerate(lines) if head.match(l)), None)
    if start is None:
        return lines, 0
    # The signature ends at the first line whose depth returns to 0 and ends in ':'.
    depth, i = 0, start
    while True:
        depth = scan_depth(lines[i], depth)
        if depth <= 0 and lines[i].rstrip().endswith(":"):
            break
        i += 1
    body = i + 1
    sig = "".join(lines[start:body])
    end = body
    while end < len(lines) and (not lines[end].strip() or lines[end].startswith(TAB) or lines[end].startswith("#")):
        end += 1
    while end > body and (lines[end - 1].strip() == "" or not lines[end - 1].startswith(TAB)):
        end -= 1
    out = lines[:body]
    out.append(TAB + 'var __pl = %s.new("%s.%s")' % (PERF, cls, fn) + NL)
    depth, cont, count = 0, False, 0
    for k in range(body, end):
        l = lines[k]
        s = l.strip()
        top = (depth == 0 and not cont and l.startswith(TAB) and not l.startswith(TAB + TAB)
               and s and not s.startswith("#") and not re.match(r"(elif|else)\b", s))
        if top:
            label = re.sub(r"\s+", " ", s)[:70].replace("\\", "/").replace('"', "'")
            out.append(TAB + '__pl.lap("L%d %s")' % (k + 1, label) + NL)
            count += 1
        out.append(l)
        if s and not s.startswith("#"):
            depth = scan_depth(l, depth)
            cont = l.rstrip().endswith("\\")
    out.append(NL + NL)
    out.append(wrapper(sig, fn))
    out.extend(lines[end:])
    out[start] = out[start].replace("func " + fn, "func " + fn + "__lapped", 1)
    return out, count


def split_top(text):
    parts, depth, cur, q = [], 0, "", None
    for c in text:
        if q:
            cur += c
            if c == q:
                q = None
            continue
        if c in "\"'":
            q = c
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c == "," and depth == 0:
            parts.append(cur)
            cur = ""
            continue
        cur += c
    if cur.strip():
        parts.append(cur)
    return parts


def wrapper(sig, fn):
    """The function under its own name: calls fn__lapped, then closes its last lap."""
    flat = " ".join(x.strip() for x in sig.splitlines())
    open_i = flat.index("(", flat.index("func"))
    depth, j = 0, open_i
    while True:
        if flat[j] == "(":
            depth += 1
        elif flat[j] == ")":
            depth -= 1
            if depth == 0:
                break
        j += 1
    params = [re.split(r"[:=]", x.strip(), maxsplit=1)[0].strip() for x in split_top(flat[open_i + 1:j])]
    void = re.search(r"->\s*void\b", flat[j + 1:]) is not None
    call = "%s__lapped(%s)" % (fn, ", ".join(params))
    close = TAB + PERF + ".close_top()" + NL
    w = sig.rstrip() + NL
    if void:
        w += TAB + call + NL + close
    else:
        w += TAB + "var __r = " + call + NL + close + TAB + "return __r" + NL
    return w


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

        def at(fn):
            m = func_re(fn)
            return next((i for i, l in enumerate(lines) if m.match(l)), -1)

        # Last function first, so each label keeps the line number of the real file.
        for fn in sorted(fns, key=at, reverse=True):
            lines, n = instrument(lines, fn, cls)
            print("LAPS %s.%s: %s" % (cls, fn, ("%d statements" % n) if n else "not in this tree"))
        p.open("w", encoding="utf-8", newline="").write("".join(lines))


if __name__ == "__main__":
    main()
