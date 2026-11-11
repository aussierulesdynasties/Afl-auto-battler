"""Boundary rules: what may never reach the sim or the state, and two export settings. Moved
from the Godot suites on 2026-11-12, rule for rule (each names the suite it came from).
"""
from common import Finding, gd_files, read

# [rule, files (or a folder walk), banned substrings, why]. A walk is ("dir", recursive).
BANNED = [
    ("no-coach-effects", ["scripts/sim/Prospects.gd", "scripts/sim/MatchSim.gd", "scripts/sim/ClubLife.gd",
                          "scripts/sim/Potential.gd", "scripts/sim/Season.gd"],
     ["Coaches.", "GameState.coaches", "club_staff("],
     "development, matches and morale do not read coaches yet (from test_coaches _test_no_effects_yet)"),
    ("no-family-in-sim", [("scripts/sim", False), ("scripts/state", False)], ["PlayerRelations"],
     "no simulation or state script reads family ties (from family _test_relations)"),
    ("no-culture-sheet", [("scripts", True)], ["CultureSheet"],
     "nothing in the game opens the old Culture sheet (from roles _test_culture_ui_tests)"),
    ("old-club-lines-presentation", ["scripts/sim/MatchSim.gd"], ["OldClubLines", "old_club_lines"],
     "old club lines are presentation only: the match never reads them (from matchup _test_old_club_rules)"),
]

PRESETS = "export_presets.cfg"
# [rule, must contain, must not contain, why]
PRESET_LINES = [
    ("web-keyboard", "html/experimental_virtual_keyboard=true", "html/experimental_virtual_keyboard=false",
     "the web export has the phone keyboard switched on (godotengine/godot#99602; from keyboard _test_preset)"),
    ("android-backup", "user_data_backup/allow=true", None,
     "the Android export turns on the system's own backup of the save (from career_ui _test_menu_and_career)"),
]


def _files(root, spec):
    out = []
    for s in spec:
        if isinstance(s, tuple):
            out += gd_files(root, s[0], recursive=s[1])
        else:
            out.append(s)
    return out


def check(root, banned=None):
    out = []
    for rule, spec, words, why in (BANNED if banned is None else banned):
        for path in _files(root, spec):
            text = read(root, path)
            if not text:
                out.append(Finding(path, 0, rule, "file not found or empty: update tools/lint/boundaries.py"))
                continue
            for n, line in enumerate(text.split("\n"), 1):
                for w in words:
                    if w in line:
                        out.append(Finding(path, n, rule, "%s: names %s" % (why, w)))
    return out


def check_presets(root):
    text = read(root, PRESETS)
    out = []
    for rule, need, never, why in PRESET_LINES:
        if need not in text:
            out.append(Finding(PRESETS, 0, rule, "missing %s: %s" % (need, why)))
        if never and never in text:
            out.append(Finding(PRESETS, text.count("\n", 0, text.find(never)) + 1, rule, "%s is set: %s" % (never, why)))
    return out


CHECKS = [check, check_presets]
