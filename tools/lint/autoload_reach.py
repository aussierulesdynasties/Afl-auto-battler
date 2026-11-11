"""The compile rule Godot only enforces at run time: a script started with `godot --script`
(`extends SceneTree`: every test runner, balance worker, audit and capture harness) compiles
BEFORE the autoloads exist, so if it names, at compile time, an autoload or a class whose
compile chain reaches one (StoryDeck -> StoryEngine -> GameState, ClubForge -> GameDB), it fails
with "Identifier not found: GameDB". Godot then hangs instead of exiting: the suite burns its
whole timeout (3000 s on run_on_github.yml, 2026-11-11). The fix is load() by path inside
_run() after `await process_frame` (afl-godot-tests skill).

This finds those names with no Godot, in about a second: it reads the [autoload] names from
project.godot, maps each class_name to its file, strips strings and comments, and follows
class names and preloads transitively. A `var`/`const` of the same name (var BigCalls = load(...))
shadows the class and is skipped. tools/ci_preflight_compile.sh (Godot --check-only) stays the
ground truth; this is the fast first gate, and the one that runs where no preflight does.
"""
import os
import re
import subprocess

from common import Finding

STR = re.compile(r'"""[\s\S]*?"""|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'')
IDENT = re.compile(r'(?<![\w.$])([A-Z]\w*)\b')
PRELOAD = re.compile(r'preload\(\s*"res://([^"]+\.gd)"')
LOCAL = re.compile(r'\b(?:var|const)\s+([A-Z]\w*)')


def strip(t):
    """The source with every string emptied and every comment removed."""
    return re.sub(r'#[^\n]*', '', STR.sub('""', t))


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

    def deps(f):
        local = set(LOCAL.findall(src[f]))
        names = {n for n in IDENT.findall(src[f]) if (n in autoloads or n in cls_of) and n not in local}
        return names, set(PRELOAD.findall(raw[f]))

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
        memo[f] = out
        return out

    findings = []
    entries = 0
    for f in sorted(src):
        if not re.search(r'^extends\s+SceneTree', raw[f], re.M):
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
            word = re.compile(r'(?<![\w.])' + re.escape(n.split('/')[-1]) + r'\b')
            ln = next((i + 1 for i, l in enumerate(lines) if word.search(strip(l))), 0) \
                or next((i + 1 for i, l in enumerate(lines) if n in l and "preload" in l), 0)
            findings.append(Finding(f, ln, "autoload-reach",
                                    "names %s at compile time (%s), so `godot --script` fails before the autoloads "
                                    "exist and the run hangs: load() it by path inside _run() after await "
                                    "process_frame" % (n, " -> ".join(chain))))
    check.entries = entries
    check.classes = len(cls_of)
    return findings


CHECKS = [check]
