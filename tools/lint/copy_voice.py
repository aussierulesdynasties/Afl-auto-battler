"""The copy voice (director, 2026-11-10: option B, the senior coach's briefing; style guide §5.1).

Moved from tests/run_copy_rules_tests.gd (_test_sources, _test_hub_pass) on 2026-11-12, rule for
rule. One banned list, scripts/core/CopyRules.gd (WORDS), walked over every copy source: story
cards, the tale phrase banks and the string literals of the UI, sim and state scripts. A known
hit sits in ALLOW with the copy pass that clears it (docs/TODO.md); the count must match
exactly, so a new hit fails and a fixed one makes its ALLOW entry shrink in the same PR. Each
screen pass pins its rewritten lines (HUB_NEW / HUB_OLD). CopyRules.words_in/check themselves
are unit-tested in Godot (tests/run_clublink_tests.gd, _test_copy_rules).
"""
import json
import re

from common import Finding, gd_const_strings, gd_files, is_comment, line_of, read

COPY_RULES = "scripts/core/CopyRules.gd"
## data/tales holds the phrase banks of the story layer (a career, the league news, a season's
## shape): every phrase there reaches the screen, so the banks are walked like the story cards.
SOURCES = ["data/stories", "data/tales", "scripts/ui", "scripts/sim", "scripts/state"]
## The phrase banks that must be among the files read (a moved or renamed bank fails by name).
TALES = ["data/tales/career.json", "data/tales/league.json", "data/tales/season.json"]

## Known hits, per file: [count, words, the pass that rewrites them]. Each reason names its copy
## voice row in docs/TODO.md (131-140, the screen passes).
ALLOW = {
    "data/stories/leadership.json": [1, "should", "row 140: a player's own question, reported"],
    "data/stories/media.json": [2, "should", "row 140: a pundit's view, reported"],
    "scripts/sim/MatchSim.gd": [1, "should", "row 131: a shot's likelihood at the gate"],
    "scripts/sim/PlanTraits.gd": [1, "starters", "kept: the Fast Starters trait (a side that starts quickly, AFL usage), not the line-up sense"],
    "scripts/sim/SkipOrders.gd": [2, "auto-pick", "row 134: renamed with the Auto-pick button"],
    "scripts/state/GameState.gd": [2, "starter, projection", "rows 134 and 138"],
    "scripts/ui/CoachingScene.gd": [1, "payroll", "row 134: coaching"],
    "scripts/ui/DraftScene.gd": [1, "projection", "row 136: draft"],
    "scripts/ui/OffseasonScene.gd": [1, "payroll", "row 137: contracts and trades"],
    "scripts/ui/PreSeasonScene.gd": [10, "starter", "row 136: pre-season"],
    "scripts/ui/SelectionScene.gd": [4, "auto-pick", "row 134: renamed with the Auto-pick button"],
    "scripts/ui/StatGuide.gd": [1, "projection", "row 139: stats and menus"],
    "scripts/ui/TrainingScene.gd": [1, "should", "row 135: training"],
}

HUB = "scripts/ui/HubScene.gd"
## The hub pass (copy voice pass 2): every rewritten line, and the line it replaced.
HUB_NEW = [
    "Our week", "This is home base. Who we play next is up top.",
    "Pick the side in Team. Set how we play in Coaching.",
    "The week's open jobs sit here. Tap one to go to it; it ticks when done.",
    "The list is a guide, never a gate. Play match or Sim the week, jobs left or not.",
    "Our %d list is set.", "Start the season", "No game for us in Round %d.",
    "We have a week off while the rest of the series plays on.",
    "Our finals campaign is over. Play out the series to see who lifts the cup.",
    "\"Season over\"", "We missed the top %d. Play out the finals to see who lifts the cup.",
    "\"Our coach\"", "Our %s. They have offered him the %s job.", "He weighs it %d out of 100",
    "Play the semi-finals", "Play the preliminary finals", "Play the Grand Final",
    "Playing the semi-finals...", "Playing the preliminary finals...",
    "Our pick. Whoever we take signs a rookie deal to the end of next season.",
    "Sim the week without picking and we pass.", "Sim the week...",
]
HUB_OLD = [
    "\"Your week\"", "Check the next opponent", "Each week a short list here", "whenever you are ready",
    "Your %d list is set.", "Begin season", "No game for you", "You have a week off",
    "Your finals campaign", "Season over for you", "You missed the top", "\"Your coach\"",
    "\"Your %s. They have", "%d of 100", "Play semi finals", "Play the prelims", "Play Grand Final",
    "Playing the semi finals", "Playing the prelims", "Your pick: whoever you take",
    "Simming the week...",
]

LITERAL = re.compile(r'"([^"\n]*)"')


def words_re(words):
    """CopyRules._words_re in Python: whole words or phrases, any case."""
    alts = [w.replace("-", "\\-").replace(" ", "\\s+") for w in words]
    return re.compile(r"(?i)(?<![A-Za-z])(" + "|".join(alts) + r")(?![A-Za-z])")


def words_in(rx, text):
    """CopyRules.words_in: the banned words in `text`, lower case, in order."""
    return [" ".join(p for p in m.group(1).lower().split(" ") if p) for m in rx.finditer(text)]


def json_strings(v, out):
    """Every string value (not key) in a parsed JSON document, in document order."""
    if isinstance(v, str):
        out.append(v)
    elif isinstance(v, dict):
        for k in v:
            json_strings(v[k], out)
    elif isinstance(v, list):
        for e in v:
            json_strings(e, out)


def source_strings(path, text):
    """[(line, string)] the copy check reads from one source file: every JSON string, or every
    double-quoted literal with a space in it on a non-comment line of a script."""
    out = []
    if path.endswith(".json"):
        strings = []
        json_strings(json.loads(text), strings)
        pos = 0
        for s in strings:
            # The line of this string in the file: its JSON spelling, searched from the last hit.
            key = json.dumps(s, ensure_ascii=False)[1:-1][:60]
            i = text.find(key, pos)
            if i < 0:
                i = text.find(key)
            else:
                pos = i
            out.append((text.count("\n", 0, i) + 1 if i >= 0 else 0, s))
        return out
    for n, line in enumerate(text.split("\n"), 1):
        if is_comment(line):
            continue
        for m in LITERAL.finditer(line):
            if " " in m.group(1):
                out.append((n, m.group(1)))
    return out


def check(root, allow=None, sources=None, tales=None):
    allow = ALLOW if allow is None else allow
    sources = SOURCES if sources is None else sources
    tales = TALES if tales is None else tales
    out = []
    rx = words_re(gd_const_strings(read(root, COPY_RULES), "WORDS"))
    found, hits_of, read_n = {}, {}, {}
    for d in sources:
        for path in gd_files(root, d, ext=(".gd", ".json")):
            try:
                strings = source_strings(path, read(root, path))
            except ValueError as e:
                out.append(Finding(path, 0, "copy-voice", "does not parse as JSON: %s" % e))
                continue
            read_n[path] = len(strings)
            for n, s in strings:
                hits = words_in(rx, s)
                if hits:
                    found[path] = found.get(path, 0) + len(hits)
                    hits_of.setdefault(path, []).append((n, hits, s))
    for path in sorted(found):
        allowed = allow.get(path, [0])[0]
        if found[path] != allowed:
            out.append(Finding(path, 0, "copy-voice", "%d banned words (allowed %d in tools/lint/copy_voice.py ALLOW). "
                               "Reword the line in the coach's voice (docs/VISUAL_STYLE_GUIDE.md 5.1), or, for a "
                               "known hit a copy pass will clear, change its ALLOW count." % (found[path], allowed)))
            for n, hits, s in hits_of[path]:
                out.append(Finding(path, n, "copy-voice", "%s: \"%s\"" % (", ".join(hits), s[:90])))
    for path in sorted(allow):
        if path not in found:
            out.append(Finding(path, 0, "copy-voice", "is clean now: drop it from ALLOW in tools/lint/copy_voice.py"))
    for path in tales:
        if read_n.get(path, 0) <= 0:
            out.append(Finding(path, 0, "copy-voice", "the phrase bank was not read, phrase by phrase (%d strings)" % read_n.get(path, 0)))
    return out


def check_hub(root, new=None, old=None):
    new = HUB_NEW if new is None else new
    old = HUB_OLD if old is None else old
    src = read(root, HUB)
    out = []
    if not src:
        return [Finding(HUB, 0, "hub-copy", "file not found")]
    for s in new:
        if s not in src:
            out.append(Finding(HUB, 0, "hub-copy", "the hub no longer says: %s (copy voice pass 2 pinned it)" % s))
    for s in old:
        if s in src:
            out.append(Finding(HUB, line_of(src, s), "hub-copy", "the hub says an old line again: %s" % s))
    return out
