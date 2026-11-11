"""Every static lint, in one command (tools/lint/README.md). No Godot.

    python3 -I tools/lint/lint.py                        # every rule; gdlint on every tracked .gd
    python3 -I tools/lint/lint.py --changed origin/main  # gdlint only on the .gd files changed since
    python3 -I tools/lint/lint.py --only copy-voice,autoload-reach
    python3 -I tools/lint/lint.py --list

Exit 1 when any rule finds a problem; each one prints as `path:line: [rule] message` (and as a
GitHub annotation on CI). gdlint is skipped with a note when gdtoolkit is not installed, unless
--require-gdlint (CI) is given.
"""
import argparse
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import autoload_reach  # noqa: E402
import boundaries  # noqa: E402
import copy_voice  # noqa: E402
import gdlint_gate  # noqa: E402
import screens  # noqa: E402
import story_flags  # noqa: E402
from common import ROOT  # noqa: E402

RULES = {
    "autoload-reach": autoload_reach.check,
    "copy-voice": copy_voice.check,
    "copy-pass": copy_voice.check_passes,
    "font-size-one-place": screens.check_font_size_one_place,
    "colour-cue": screens.check_colour_cues,
    "type-role": screens.check_type_roles,
    "raw-club-ink": screens.check_raw_club_ink,
    "green-decoration": screens.check_green_decoration,
    "boundaries": boundaries.check,
    "export-presets": boundaries.check_presets,
    "story-flags": story_flags.check,
}


def changed_gd(root, ref):
    base = subprocess.run(["git", "merge-base", ref, "HEAD"], cwd=root, capture_output=True, text=True).stdout.strip() or ref
    r = subprocess.run(["git", "diff", "--name-only", "--diff-filter=d", base, "--", "*.gd"], cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("git diff against %s failed: %s" % (ref, r.stderr.strip()))
    return sorted(f for f in r.stdout.split("\n") if f.endswith(".gd"))


def emit(f):
    print(f.text())
    if os.environ.get("GITHUB_ACTIONS"):
        loc = "file=%s" % f.path + (",line=%d" % f.line if f.line else "")
        print("::error %s,title=lint %s::%s" % (loc, f.rule, f.message.replace("\n", " ")))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", default="", help="comma-separated rule names (see --list); 'gdlint' for gdlint")
    ap.add_argument("--changed", metavar="REF", help="gdlint only the .gd files changed since REF")
    ap.add_argument("--require-gdlint", action="store_true", help="fail when gdtoolkit %s is missing" % gdlint_gate.VERSION)
    ap.add_argument("--write-baseline", action="store_true", help="rewrite tools/lint/gdlint_baseline.txt from a full gdlint run")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--root", default=ROOT, help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    names = list(RULES) + ["gdlint"]
    if a.list:
        print("\n".join(names))
        return 0
    only = [s.strip() for s in a.only.split(",") if s.strip()] or names
    unknown = [s for s in only if s not in names]
    if unknown:
        ap.error("unknown rule(s): %s (see --list)" % ", ".join(unknown))
    bad = 0
    for name in only:
        if name == "gdlint":
            continue
        t = time.time()
        found = RULES[name](a.root)
        for f in found:
            emit(f)
        bad += len(found)
        print("%-20s %s (%.1f s)" % (name, "ok" if not found else "%d problem(s)" % len(found), time.time() - t), file=sys.stderr)
    if "gdlint" in only:
        version = gdlint_gate.available()
        if version != gdlint_gate.VERSION:
            msg = "gdlint: gdtoolkit %s is needed (found %s): pip install -r tools/lint/requirements.txt" % (
                gdlint_gate.VERSION, version or "none")
            if a.require_gdlint or a.write_baseline:
                print("::error::" + msg if os.environ.get("GITHUB_ACTIONS") else msg)
                return 1
            print(msg + "; skipped", file=sys.stderr)
        else:
            t = time.time()
            files = autoload_reach.tracked_gd(a.root) if (a.write_baseline or not a.changed) else changed_gd(a.root, a.changed)
            found = gdlint_gate.run(a.root, files)
            if a.write_baseline:
                counts = gdlint_gate.write_baseline(found)
                print("gdlint baseline: %d problems in %d (file, rule) pairs over %d files" % (len(found), len(counts), len(files)))
            else:
                new, notes = gdlint_gate.gate(found, files)
                for f in new:
                    emit(f)
                for n in notes:
                    print("note: " + n, file=sys.stderr)
                bad += len(new)
                print("%-20s %s over %d files (%.1f s)" % ("gdlint", "ok" if not new else "%d new problem(s)" % len(new),
                                                           len(files), time.time() - t), file=sys.stderr)
    if bad:
        print("%d lint problem(s). Each line above names the file, the line and the rule; tools/lint/README.md says "
              "where each rule lives." % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
