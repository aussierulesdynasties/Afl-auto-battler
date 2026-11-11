"""Shared helpers for the static lints (tools/lint/README.md). Standard library only.

A finding is (path, line, rule, message): path is relative to the repo root with forward
slashes, line is 1-based (0 when the rule is about the whole file).
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


class Finding(tuple):
    __slots__ = ()

    def __new__(cls, path, line, rule, message):
        return tuple.__new__(cls, (path, int(line), rule, message))

    path = property(lambda s: s[0])
    line = property(lambda s: s[1])
    rule = property(lambda s: s[2])
    message = property(lambda s: s[3])

    def text(self):
        where = "%s:%d" % (self.path, self.line) if self.line else self.path
        return "%s: [%s] %s" % (where, self.rule, self.message)


def read(root, rel):
    """A repo file's text ("" when it is missing), newlines as \\n."""
    try:
        with open(os.path.join(root, rel), encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def gd_files(root, rel_dir, recursive=True, ext=(".gd",)):
    """Repo-relative paths of the files under rel_dir with one of the extensions, sorted.
    Folders starting with "." are skipped, as the Godot suites' walkers did."""
    out = []
    base = os.path.join(root, rel_dir)
    if not os.path.isdir(base):
        return out
    if recursive:
        for d, subs, files in os.walk(base):
            subs[:] = [s for s in subs if not s.startswith(".")]
            for f in files:
                if f.endswith(ext):
                    out.append(os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/"))
    else:
        for f in os.listdir(base):
            if f.endswith(ext) and os.path.isfile(os.path.join(base, f)):
                out.append((rel_dir.rstrip("/") + "/" + f))
    return sorted(out)


def is_comment(line):
    return line.strip().startswith("#")


def line_of(text, needle, start=0):
    """1-based line of the first `needle` in `text` (0 when absent)."""
    i = text.find(needle, start)
    return text.count("\n", 0, i) + 1 if i >= 0 else 0


def gd_const_strings(text, name):
    """The string items of `const NAME := [ ... ]` in a GDScript source."""
    m = re.search(r"^const\s+%s\s*:?=\s*\[(.*?)\]" % re.escape(name), text, re.S | re.M)
    if not m:
        raise ValueError("const %s not found" % name)
    return re.findall(r'"((?:\\.|[^"\\])*)"', m.group(1))


def gd_const_ints(text, name):
    """The int items of `const NAME := [A, 12, B]`, resolving bare names through `const A := 11`."""
    m = re.search(r"^const\s+%s\s*:?=\s*\[(.*?)\]" % re.escape(name), text, re.S | re.M)
    if not m:
        raise ValueError("const %s not found" % name)
    out = []
    for item in [s.strip() for s in m.group(1).split(",") if s.strip()]:
        if item.isdigit():
            out.append(int(item))
            continue
        c = re.search(r"^const\s+%s\s*:?=\s*(\d+)\b" % re.escape(item), text, re.M)
        if not c:
            raise ValueError("const %s (in %s) is not an int constant" % (item, name))
        out.append(int(c.group(1)))
    return out
