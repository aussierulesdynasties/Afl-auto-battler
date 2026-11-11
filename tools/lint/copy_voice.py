"""The copy voice (director, 2026-11-10: option B, the senior coach's briefing; style guide §5.1).

Moved from tests/run_copy_rules_tests.gd (_test_sources, _test_hub_pass, _test_team_pass, _test_training_pass) on 2026-11-12, rule for
rule. One banned list, scripts/core/CopyRules.gd (WORDS), walked over every copy source: story
cards, the tale phrase banks and the string literals of the UI, sim and state scripts. A known
hit sits in ALLOW with the copy pass that clears it (docs/TODO.md); the count must match
exactly, so a new hit fails and a fixed one makes its ALLOW entry shrink in the same PR. Each
screen pass pins its rewritten lines and the ones they replaced (PASSES). CopyRules.words_in/check themselves
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
    # Auto-pick is the Team selection button's name (director, 2026-11-12: "Auto pick. I already answered
    # this question"); these lines name the button, so the word stays.
    "scripts/sim/SkipOrders.gd": [2, "auto-pick", "kept: names the Auto-pick button (director, 2026-11-12)"],
    "scripts/state/GameState.gd": [1, "projection", "row 138"],
    "scripts/ui/DraftScene.gd": [1, "projection", "row 136: draft"],
    "scripts/ui/FirstVisitIntro.gd": [1, "auto-pick", "kept: names the Auto-pick button (director, 2026-11-12)"],
    "scripts/ui/OffseasonScene.gd": [1, "payroll", "row 137: contracts and trades"],
    "scripts/ui/PreSeasonScene.gd": [10, "starter", "row 136: pre-season"],
    "scripts/ui/SelectionScene.gd": [5, "auto-pick", "kept: the Auto-pick button and the lines that name it (director, 2026-11-12)"],
    "scripts/ui/StatGuide.gd": [1, "projection", "row 139: stats and menus"],
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

## The team builder and coaching pass (copy voice pass 5, with the builder's tap hint, the trait
## picker's none line and the sim sheet's plan line): per file, the rewritten lines and the
## lines they replaced. The button stays Auto-pick (director, 2026-11-12: "Auto pick. I already answered
## this question"), so its lines name it in the coach's voice.
TEAM_PASS = {
    "scripts/ui/SelectionScene.gd": [[
        "\"Auto-pick\"", "Dual ruck on. Auto-pick names a second ruck on the bench.",
        "One ruck. Auto-pick fills the bench with the best of the rest.",
        "Our side is confirmed for this week.", "\"Our team\"",
        "Projected: %s as they would line up this week. They name their side on match day. They kick the other way.",
        "Auto-pick names our side until you move someone.",
        "Saved as your Best 23. Choose it any week from Auto-pick.",
        "Back to our side from before Auto-pick.",
        "Leave the player out while he is fit and the promise breaks. It stings.",
    ], ["Dual ruck on: Auto-pick", "One ruck: Auto-pick", "Side confirmed for", "\"Your team\"", "(projected:",
        "Picked for you", "Back to your side before the auto-pick", "Leave a fit player out"]],
    "scripts/ui/CoachingScene.gd": [[
        "Each plan buys an edge and gives something up. The note below says which.",
        "Each plan runs on one of our list's strengths. That is our side as picked, against every list in the league.",
        "\"Also on our list\"", "After three games, how we win and get beaten shows here.",
        "One strength and one cost, on top of our plan, every match. Or none.",
        "No part of our game is costing us regularly.", "No one part of our game stands above the league.",
        "%s of the %s salary cap",
    ], ["gives something up;", "one of your list's", "Also on your list", "how your side wins", "on top of your plan",
        "of your game", "payroll %s"]],
    "scripts/ui/FirstVisitIntro.gd": [[
        "Our match-day 23 for this week. Auto-pick names it until you move someone.",
        "Move players on and off the ground to set the side you want.",
        "Our game plan: how we play every week, set against what our list is good at.",
        "Each plan suits some lists more than others. We can change it before any match.",
    ], ["Your match-day 23", "is picked for you", "the team you want", "Your game plan: how your side",
        "Pick the plan that suits"]],
    "scripts/sim/SkipOrders.gd": [[
        "Auto-pick names the side in place of one you named.",
        "Auto-pick names the side in place of one you named, and keeps naming it for the finals until you name another.",
    ], ["Auto-pick replaces"]],
    "scripts/state/GameState.gd": [[
        "Nobody needs a break. This is our best side.", "Not enough fresh players to rest anyone. This is our best side.",
        "No saved Best 23 yet. Set a side and save it.", "Our Best 23. Replacing unavailable players: %s.",
        "\"Our Best 23.\"", "No young player is close enough to take a senior spot. This is our best side.",
    ], ["this is your best side", "arrange a side and save it", "\"Your Best 23", "a starter's spot"]],
    "scripts/ui/TeamBuilder.gd": [[
        " two of our players to swap them. Or drag one onto the other.",
    ], [" a player, then another (or drag one onto another) to swap them."]],
    "scripts/sim/PlanTraits.gd": [[
        "No trait. Just our game plan.",
    ], ["No trait: your game plan as written."]],
    "scripts/ui/SimOrdersSheet.gd": [[
        "Every match starts on our game plan: %s.\\nWe can change it in How we play.",
    ], ["Every match starts on your game plan", ": change it in How we play."]],
}

TRAINING = "scripts/ui/TrainingScene.gd"
## The training pass (copy voice pass 6): the rewritten lines of TrainingScene.gd, and the lines
## they replaced. What a player trains as is his development focus, on every line that names it.
TRAINING_NEW = [
    "A player earns development every game. His development focus decides which stats it lifts.",
    "Pick the kind of footballer each player becomes. That is his development focus.",
    "By position trains what a player's position is judged on. Change a focus any time.",
    "Nothing develops a player like senior football. A fit player we leave out develops in the reserves, at about half the rate.",
    "Young players a long way short of their potential improve quicker than the rest.",
    "No rating moved after the last game.", "No game played yet. Our players develop after every game.",
    "Focus changed. Banked development lifted his OVR from %d to %d.",
    "Focus changed. Banked development went straight into it.", "Focus changed. It starts after the next game.",
    "%s set for %d %s.", "last game. A senior game is worth up to %d.",
    "On hold while he learns a position. All his training goes into the new role.",
    "His development drills get the rest. Change it when the %d season opens.",
    "Each point on one stat costs more as it climbs. So his OVR grows more slowly than with no stat focus.",
    "As a %s he rates %d. In his own position, %d. ", "That is up to the standard. He can be picked there after week %d.",
    "Get within %d by week %d and he can be picked there.",
]
TRAINING_OLD = [
    "should become", "safe default", "whenever you like", "Fit players you leave out", "improve quickest",
    "Training: no rating changes", "Players develop after every match", "what he is developing as",
    "Development changed", "lifted him from", "applied to %d", "spent under the new focus",
    "(a senior game", "learns a position:", "You can change it when", "get dearer", "on his plan alone",
    "further past its line", "his own game %d", "\"up to the standard", "\"within %d by week",
]

## Every pinned pass: (file, the pass, its rewritten lines, the lines they replaced).
PASSES = [(HUB, "copy voice pass 2, hub", HUB_NEW, HUB_OLD)] + [
    (path, "copy voice pass 5, team and coaching", v[0], v[1]) for path, v in TEAM_PASS.items()] + [
    (TRAINING, "copy voice pass 6, training", TRAINING_NEW, TRAINING_OLD)]

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


## Phone first: a line of copy says "tap", never "click". A screen that names the pointer by
## device asks ScreenLayout.tap_word() (a one-word literal, so the scan passes it).
CLICK = re.compile(r"(?i)(?<![A-Za-z])click(s|ed|ing)?(?![A-Za-z])")


def check_no_click(root, sources=None):
    """No copy source has a line with "click" in it (moved from copy_rules _test_no_click)."""
    out = []
    for d in (SOURCES if sources is None else sources):
        for path in gd_files(root, d, ext=(".gd", ".json")):
            try:
                strings = source_strings(path, read(root, path))
            except ValueError:
                continue  # copy-voice reports the broken JSON
            for n, s in strings:
                if CLICK.search(s):
                    out.append(Finding(path, n, "no-click", "copy says 'tap', not 'click': \"%s\"" % s[:90]))
    return out


def check_passes(root, passes=None):
    """Each copy pass's rewritten lines are still in their file, and none of the old ones."""
    out = []
    for path, label, new, old in (PASSES if passes is None else passes):
        src = read(root, path)
        if not src:
            out.append(Finding(path, 0, "copy-pass", "file not found (%s pinned it)" % label))
            continue
        for s in new:
            if s not in src:
                out.append(Finding(path, 0, "copy-pass", "no longer says: %s (%s pinned it)" % (s, label)))
        for s in old:
            if s in src:
                out.append(Finding(path, line_of(src, s), "copy-pass", "says an old line again: %s (%s)" % (s, label)))
    return out
