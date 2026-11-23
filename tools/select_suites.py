"""Which test suites does a pull request need? Derived from the code, no list kept by hand.

Each suite runner (tests/run_<suite>_tests.gd) reaches res:// scripts and scenes through
preload/load paths, scene references and class names (class_name lines, plus the autoloads
in project.godot, found by name anywhere in a file, strings included: get_node("GameState")).
A changed file selects every suite whose closure contains it, plus the smoke set.

  python3 tools/select_suites.py --base origin/main   # suites for the files changed since base
  python3 tools/select_suites.py --files a.gd b.gd    # same for named files
  python3 tools/select_suites.py --closures           # every suite's size, for a look

Anything that cannot be traced goes to the full wall: data/, project.godot, export presets,
the test harness (tests/functions_ran.gd, tests/tap.gd, the fixture runners, tools/run_tests.sh),
the files that plan the run (RUN_PLAN), every tool the suites or the run script name by path (and
the tools those name in turn, following code only, never notes), a deleted file something still
names, and any game file type the walker does not follow. A fixture the suites read by its res://
path is traced like an asset. A file outside the game that no suite reads (another workflow,
.gitignore, a one-off tool) and a deleted file nothing names select the smoke set only: the lint
and data checks run in full on every pull request anyway.
Pushes to main and the merge queue never call this: they run the full wall.
"""
import argparse
import json
from collections import deque
import pathlib
import re
import subprocess
import sys

from ci_shards import ROOT, discover

# The always-on set: the broadest quick suites (measured seconds in tools/ci_suite_timings.json),
# so a break the walker cannot see still shows up in a PR run.
SMOKE = ("chronology", "career_ui", "ratings")

REACH = 1  # a suite covers a script its own files name (a hop of 1), not what that script calls in turn
FOLLOWED = (".gd", ".tscn", ".tres", ".gdshader", ".uid")
# Leaf resources: referenced from scripts and scenes, never a source of further references.
LEAF_DIRS = ("assets/",)
# Suites that find their files by listing a folder at run time (DirAccess), so no path names them and the
# walker cannot see the link: a change under the folder selects the suite. ground_seats checks every
# assets/grounds/<slug>/seats_*.bin against its model (tools/grounds/seat_rule.gd: SeatRule.grounds());
# without this a ground's new seats or model ran no seat check before the merge queue.
SCANNED = {"assets/grounds/": ("ground_seats",)}
IDENT = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
RES = re.compile(r"res://[A-Za-z0-9_./\- ]*[A-Za-z0-9_./\-]")
CLASS_NAME = re.compile(r"^\s*class_name\s+([A-Za-z_][A-Za-z0-9_]*)", re.M)


def rel(path, root):
    return path.relative_to(root).as_posix()


def project_files(root):
    skip = {".git", ".godot", ".claude", "node_modules"}
    out = []
    for p in root.rglob("*"):
        if p.is_file() and not (skip & set(p.relative_to(root).parts)):
            out.append(rel(p, root))
    return sorted(out)


def autoloads(root):
    names = {}
    text = (root / "project.godot").read_text(errors="replace")
    section = ""
    for line in text.splitlines():
        if line.startswith("["):
            section = line.strip("[]")
        elif section == "autoload" and "=" in line:
            name, _, value = line.partition("=")
            path = value.strip().strip('"').lstrip("*")
            if path.startswith("res://"):
                names[name.strip()] = path[len("res://"):]
    return names


def build_graph(root=ROOT):
    """Returns (edges {file: set(files)}, files). Over-reaching is safe, missing an edge is not."""
    files = project_files(root)
    fileset = set(files)
    classes = dict(autoloads(root))
    for f in files:
        if f.endswith(".gd"):
            for name in CLASS_NAME.findall((root / f).read_text(errors="replace")):
                classes[name] = f
    edges = {}
    for f in files:
        if not f.endswith((".gd", ".tscn", ".tres", ".gdshader")):
            continue
        text = (root / f).read_text(errors="replace")
        deps = set()
        for literal in RES.findall(text):
            path = literal[len("res://"):]
            if path in fileset:
                deps.add(path)
            elif path:  # a path built at run time ("res://scenes/" + name): every file under that prefix
                deps.update(x for x in files if x.startswith(path))
        if f.endswith(".gd"):
            for line in text.splitlines():
                if line.lstrip().startswith("#"):
                    continue
                for ident in IDENT.findall(line):
                    if ident in classes:
                        deps.add(classes[ident])
        deps.discard(f)
        edges[f] = deps
    return edges, files


def distances(start, edges, autoload_files):
    """Fewest script hops from a suite's runner to each file. A hop is a script naming another
    script; the test files themselves, scenes and resources are free (a scene is its scripts), the
    Router (the screen table) is free for a suite that names it, and the other autoloads are left out:
    every suite names GameState and GameDB, and through them every suite would reach the whole sim."""
    dist, queue = {start: 0}, deque([start])
    router = next((f for f in autoload_files if f.endswith("/Router.gd")), None)
    while queue:
        node = queue.popleft()
        for dep in edges.get(node, ()):
            if dep in autoload_files and dep != router:
                continue
            free = (node.startswith("tests/") and dep.startswith("tests/")) or dep.endswith((".tscn", ".tres"))                 or node.endswith((".tscn", ".tres")) or node == router
            step = dist[node] + (0 if free else 1)
            if step < dist.get(dep, 99):
                dist[dep] = step
                (queue.appendleft if free else queue.append)(dep)
    return dist


def suite_distances(root=ROOT):
    edges, files = build_graph(root)
    auto = set(autoloads(root).values())
    return {s: distances(f"tests/run_{s}_tests.gd", edges, auto) for s in discover(root)}, files, auto


# Where the game and its test run live. A changed file outside these that nothing the test run
# reads names (.gitignore, another workflow, a licence note, a one-off tool) cannot change a
# suite's result, so it selects only the smoke set (director 2026-11-16: pull requests run the
# tests related to their change; the merge queue runs the full wall before anything lands).
GAME = ("scripts/", "scenes/", "assets/", "data/", "tests/", "addons/", "project.godot", "export_presets.cfg")
# What decides which suites run and how: a change here runs every suite.
RUN_PLAN = (".github/workflows/tests.yml", "tools/run_tests.sh", "tools/list_suites.sh", "tools/ci_shards.py",
            "tools/ci_shards.txt", "tools/ci_long_suites.txt", "tools/select_suites.py", ".gitattributes")
# Never read by a suite: git's ignore list and the other workflows. The lint, data and planner checks
# (the lint and preflight jobs) run in full on every pull request whatever is selected here.
NEVER_READ = (".gitignore", ".github/", ".claude/")
# Code the suites run can name further tools; only code is followed, never notes or data.
CODE = (".sh", ".py", ".gd")
# Fixtures that are data, read by the suites through res:// paths: traced like assets.
FIXTURE_DATA = (".txt", ".gz", ".csv", ".json", ".save")


PATHS = re.compile(r"[\w./-]+")
WORD = re.compile(r"[\w.-]+")


def paths_in(text):
    """Every path-like word in text (res:// and a leading ./ or / dropped, trailing dots dropped)."""
    return {w.removeprefix("./").lstrip("/").rstrip(".") for w in PATHS.findall(text.replace("res://", " "))}


def words(text):
    """Every file-name-like word in text (a path splits at its slashes), trailing dots dropped."""
    return {w.rstrip(".") for w in WORD.findall(text)}


def run_reach(root, files):
    """(The tools outside GAME that the suites or the run script name by path, directly or through
    one another; the paths those files name, to look a deleted tool up in; the res:// paths the
    game names, for a root file such as the project icon). Naming too much only runs more suites."""
    text_of = lambda p: (root / p).read_text(errors="replace") if (root / p).is_file() else ""
    sources = ["tools/run_tests.sh"] + [f for f in files if f.startswith("tests/") and f.endswith(".gd")]
    candidates = {f for f in files if not f.startswith(GAME) and not f.startswith(NEVER_READ)}
    reached, frontier, seen = set(sources), list(sources), set()
    while frontier:
        new_paths = set().union(*(paths_in(text_of(f)) for f in frontier if f.endswith(CODE))) - seen
        seen |= new_paths
        frontier = [c for c in new_paths & candidates if c not in reached]
        reached.update(frontier)
    res_paths = set()
    for f in files:
        if f.startswith(GAME) and f.endswith((".gd", ".tscn", ".tres", ".godot", ".cfg")):
            res_paths.update(m[len("res://"):] for m in RES.findall(text_of(f)))
    return reached, seen, res_paths


def mentioned(path, root, files):
    """Does any game file still name a deleted file (its file name or class name, as a word)?"""
    name = pathlib.PurePosixPath(path).name
    wanted = {name, name.split(".")[0]}
    for f in files:
        if f.startswith(GAME) and f.endswith((".gd", ".tscn", ".tres", ".gdshader", ".godot", ".cfg")):
            if wanted & words((root / f).read_text(errors="replace")):
                return True
    return False


def select(changed, root=ROOT, smoke=SMOKE):
    """Returns (suites, why). why is non-empty when the whole wall must run."""
    dists, files, auto = suite_distances(root)
    suites = set(dists)
    wanted = {s for s in smoke if s in suites}
    reach = None
    for path in changed:
        base = path[:-len(".uid")] if path.endswith(".uid") else path
        if path.startswith(("docs/", "tools/audit/", "tools/visual/", "tools/lint/")) or path.endswith(".md"):
            continue
        if not base.startswith(GAME):
            if base in RUN_PLAN:
                return sorted(suites), f"{path} decides which suites run"
            if base.startswith(NEVER_READ):
                continue  # no suite reads it: the smoke set covers it
            reach = reach if reach is not None else run_reach(root, files)
            reached, run_paths, res_paths = reach
            if base in reached or base in run_paths or base in res_paths:
                return sorted(suites), f"{path} is read by the suites"
            continue  # nothing the suites read: the smoke set covers it
        fixture = base.startswith("tests/fixtures/") and base.endswith(FIXTURE_DATA)
        harness = base.startswith(("tests/fixtures/", "tests/functions_ran", "tests/tap", "tests/export_data")) and not fixture
        traced = (base.startswith("tests/") and base.endswith(".gd") and not harness) or fixture \
            or (base.startswith(("scripts/", "scenes/")) and base.endswith(FOLLOWED)) or base.startswith(LEAF_DIRS)
        if base not in files:
            if base.startswith(("scripts/", "scenes/", "assets/", "tests/")) and not harness \
                    and not mentioned(base, root, files):
                continue  # deleted, and nothing left names it
            return sorted(suites), f"{path} was deleted or renamed and is still named"
        if not traced:
            return sorted(suites), f"{path} cannot be traced to suites"
        if base in auto:
            return sorted(suites), f"{path} is an autoload every suite loads"
        wanted |= {s for s, d in dists.items() if d.get(base, 99) <= REACH}
        wanted |= {s for folder, by in SCANNED.items() if base.startswith(folder) for s in by if s in suites}
    return sorted(wanted), ""


def changed_files(base):
    merge_base = subprocess.run(["git", "merge-base", base, "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    out = subprocess.run(["git", "diff", "--name-only", merge_base, "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [line for line in out.splitlines() if line]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base")
    parser.add_argument("--files", nargs="*")
    parser.add_argument("--closures", action="store_true")
    parser.add_argument("--json", action="store_true", help='print {"suites", "partial", "note"} (the CI plan job)')
    args = parser.parse_args()
    if args.closures:
        dists, _, _ = suite_distances()
        for s, d in sorted(dists.items(), key=lambda kv: len(kv[1])):
            print(f"{s:14} {sum(1 for v in d.values() if v <= REACH)} files covered")
        return 0
    changed = args.files if args.files is not None else changed_files(args.base or "origin/main")
    suites, why = select(changed)
    note = "full wall: " + why if why else f"{len(suites)} of {len(discover())} suites"
    if args.json:
        print(json.dumps({"suites": " ".join(suites), "partial": len(suites) < len(discover()), "note": note}))
    else:
        print(" ".join(suites))
        print(note, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
