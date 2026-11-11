"""The compile rule Godot only enforces at run time: a script started with `godot --script`
(`extends SceneTree`: every test runner, balance worker, audit and capture harness) compiles
BEFORE the autoloads exist, so if it names, at compile time, an autoload or a class whose
compile chain reaches one (StoryDeck -> StoryEngine -> GameState, ClubForge -> GameDB), it fails
with "Identifier not found: GameDB". Godot then hangs instead of exiting: the suite burns its
whole timeout (3000 s on run_on_github.yml, 2026-11-11). The fix is load() by path inside
_run() after `await process_frame` (afl-godot-tests skill).

This finds those names with no Godot, in about a second: it reads the [autoload] names from
project.godot, maps each class_name to its file, strips strings and comments, and follows
class names, preloads and `extends "res://..."` bases transitively. A `var`/`const` of the same
name (var BigCalls = load(...)) shadows the class: a class-level one in the whole file, one inside a
function only in that function. An entry script is one whose extends chain reaches SceneTree. tools/ci_preflight_compile.sh (Godot --check-only) stays the
ground truth; this is the fast first gate, and the one that runs where no preflight does.
"""
import os
import re
import subprocess

from common import Finding

# One pass, left to right, so a quote inside a comment and a # inside a string both read right.
# A double-quoted string may run over a line break: Godot accepts it (tests/run_matchday_tests.gd).
TOKEN = re.compile(r'#[^\n]*|"""[\s\S]*?"""|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\\n])*\'')
IDENT = re.compile(r'(?<![\w.$])([A-Z]\w*)\b')
PRELOAD = re.compile(r'preload\(\s*["\']res://([^"\']+\.gd)["\']')
EXTENDS_PATH = re.compile(r'^extends\s+["\']res://([^"\']+\.gd)["\']', re.M)
EXTENDS_NAME = re.compile(r'^extends\s+(\w+)', re.M)
LOCAL = re.compile(r'\b(?:var|const)\s+([A-Z]\w*)')
CLASS_LOCAL = re.compile(r'^(?:static\s+)?(?:var|const)\s+([A-Z]\w*)', re.M)
FUNC_START = re.compile(r'^(?:static\s+)?func\b')


def strip(t):
    """The source with every string emptied and every comment removed."""
    def blank(m):
        s = m.group(0)
        return "" if s.startswith("#") else '"' + "\n" * s.count("\n") + '"'
    return TOKEN.sub(blank, t)


def tracked_gd(root):
    r = subprocess.run(["git", "ls-files", "-z", "*.gd"], cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("git ls-files failed: %s" % r.stderr.strip())
    return [f for f in r.stdout.split("\0") if f]


def autoload_names(root):
    with open(os.path.join(root, "project.godot"), encoding="utf-8") as f:
        proj = f.read()
    if "[autoload]" not in proj:
        return set()
    block = proj.split("[autoload]", 1)[1].split("\n[", 1)[0]
    return set(re.findall(r'^(\w+)="\*?res://', block, re.M))


def check(root, files=None, extra=()):
    """Findings for every SceneTree script that names an autoload-reaching class. `files` are
    repo-relative .gd paths (default: every tracked one); `extra` adds untracked ones."""
    files = list(tracked_gd(root) if files is None else files) + list(extra)
    autoloads = autoload_names(root)
    raw, src, cls_of = {}, {}, {}
    for f in files:
        try:
            with open(os.path.join(root, f), encoding="utf-8") as fh:
                raw[f] = fh.read()
        except FileNotFoundError:
            continue  # deleted in the working tree
        src[f] = strip(raw[f])
        m = re.search(r'^class_name\s+(\w+)', raw[f], re.M)
        if m:
            cls_of[m.group(1)] = f

    def blocks(f):
        """The stripped source cut at each top-level func: the class body, then one per function."""
        out, start, cur = [], 1, []
        for i, line in enumerate(src[f].split("\n")):
            if FUNC_START.match(line) and cur:
                out.append((start, cur))
                start, cur = i + 1, []
            cur.append(line)
        out.append((start, cur))
        return out

    def deps(f):
        """({name: first line naming it unshadowed}, {preloaded or extended path})."""
        class_local = set(CLASS_LOCAL.findall(src[f]))
        names = {}
        for start, lines in blocks(f):
            local = class_local | (set(LOCAL.findall("\n".join(lines))) if FUNC_START.match(lines[0]) else set())
            for i, line in enumerate(lines):
                for n in IDENT.findall(line):
                    if (n in autoloads or n in cls_of) and n not in local and n not in names:
                        names[n] = start + i
        return names, set(PRELOAD.findall(raw[f])) | set(EXTENDS_PATH.findall(raw[f]))

    entry_memo = {}

    def is_entry(f, seen=()):
        """Whether f's extends chain reaches SceneTree (so `godot --script` can start it)."""
        if f in entry_memo:
            return entry_memo[f]
        if f in seen:
            return False
        m = EXTENDS_PATH.search(raw[f])
        if m:
            out = m.group(1) in src and is_entry(m.group(1), seen + (f,))
        else:
            m = EXTENDS_NAME.search(raw[f])
            base = m.group(1) if m else ""
            out = base == "SceneTree" or (base in cls_of and cls_of[base] != f and is_entry(cls_of[base], seen + (f,)))
        if not seen:
            entry_memo[f] = out
        return out

    memo = {}

    def reach(f, seen=()):
        """The chain from file f's compile-time names to an autoload, or None."""
        if f in memo:
            return memo[f]
        if f in seen:
            return None
        names, preloads = deps(f)
        out = None
        for n in sorted(names):
            if n in autoloads:
                out = [n]
                break
        if out is None:
            for n in sorted(names):
                g = cls_of.get(n)
                if g and g != f:
                    r = reach(g, seen + (f,))
                    if r:
                        out = [n] + r
                        break
        if out is None:
            for p in sorted(preloads):
                if p in src:
                    r = reach(p, seen + (f,))
                    if r:
                        out = [p.split('/')[-1]] + r
                        break
        # A walk cut short by a cycle (an ancestor of f is in `seen`) is partial: cache it only when
        # it found a chain or started from nothing, or a later runner naming a class on the cycle passes.
        if out or not seen:
            memo[f] = out
        return out

    findings = []
    entries = 0
    for f in sorted(src):
        if not is_entry(f):
            continue
        entries += 1
        names, preloads = deps(f)
        hits = []
        for n in sorted(names):
            if n in autoloads:
                hits.append((n, [n]))
            else:
                r = reach(cls_of[n])
                if r:
                    hits.append((n, [n] + r))
        for p in sorted(preloads):
            if p in src:
                r = reach(p)
                if r:
                    hits.append((p, [p.split('/')[-1]] + r))
        lines = raw[f].split("\n")
        for n, chain in hits:
            ln = names.get(n) or next((i + 1 for i, l in enumerate(lines)
                                       if n in l and ("preload" in l or l.startswith("extends"))), 0)
            findings.append(Finding(f, ln, "autoload-reach",
                                    "names %s at compile time (%s), so `godot --script` fails before the autoloads "
                                    "exist and the run hangs: load() it by path inside _run() after await "
                                    "process_frame" % (n, " -> ".join(chain))))
    check.entries = entries
    check.classes = len(cls_of)
    return findings


CHECKS = [check]
