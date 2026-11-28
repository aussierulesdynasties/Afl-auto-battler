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
    # Auto-pick is the Team selection button's name (director, 2026-11-12: "Auto pick. I already answered
    # this question"); these lines name the button, so the word stays.
    "scripts/sim/SkipOrders.gd": [2, "auto-pick", "kept: names the Auto-pick button (director, 2026-11-12)"],

    "scripts/state/GameState.gd": [1, "projection", "row 138"],
    "scripts/ui/DraftScene.gd": [1, "projection", "row 136: draft"],
    "scripts/ui/FirstVisitIntro.gd": [1, "auto-pick", "kept: names the Auto-pick button (director, 2026-11-12)"],
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
    "Our %d list is set.", "Start the season", "No game for us in %s.",
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
    ], ["atch committee", "Dual ruck on: Auto-pick", "One ruck: Auto-pick", "Side confirmed for", "\"Your team\"", "(projected:",
        "Picked for you", "Back to your side before the auto-pick", "Leave a fit player out"]],
    "scripts/ui/CoachingScene.gd": [[
        "Each plan buys an edge and gives something up. The note below says which.",
        "Each plan runs on one of our list's strengths. That is our side as picked, against every list in the league.",
        "\"Also on our list\"", "After three games, how we win and get beaten shows here.",
        "One strength and one cost, as a plan of its own. It beats no plan and no plan beats it.",
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
    ], ["atch committee", "Auto-pick replaces"]],
    "scripts/state/GameState.gd": [[
        "Nobody needs a break. This is our best side.", "Not enough fresh players to rest anyone. This is our best side.",
        "No saved Best 23 yet. Set a side and save it.", "Our Best 23. Replacing unavailable players: %s.",
        "\"Our Best 23.\"", "No young player is close enough to take a senior spot. This is our best side.",
    ], ["this is your best side", "arrange a side and save it", "\"Your Best 23", "a starter's spot"]],
    "scripts/ui/TeamBuilder.gd": [[
        " two of our players to swap them. Or drag one onto the other.",
    ], [" a player, then another (or drag one onto another) to swap them."]],
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
    # Row 135, second pass (2026-11-15): the Learn picker added after pass 6, the carry-on line and the potential notes.
    "He can learn %s.\\nTwo of our players are learning a position already: %s.\\nHe can start when one of them finishes or stops.",
    "carries on until we lock one in for %d.", "Past his potential: every point costs far more.",
    "Close to his potential: training costs more.",
]
TRAINING_OLD = [
    "should become", "safe default", "whenever you like", "Fit players you leave out", "improve quickest",
    "Training: no rating changes", "Players develop after every match", "what he is developing as",
    "Development changed", "lifted him from", "applied to %d", "spent under the new focus",
    "(a senior game", "learns a position:", "You can change it when", "get dearer", "on his plan alone",
    "further past its line", "his own game %d", "\"up to the standard", "\"within %d by week",
    "but two players are already learning", "comes off it", "until you lock", "his projected peak",
]

## The contracts and trades pass (copy voice pass 8, with the T3.R56 trade and contract tutorials
## and the off-season brief): per file, the rewritten lines and the lines they replaced.
CONTRACTS_PASS = {
    "scripts/ui/OffseasonScene.gd": [[
        "%s of the %s salary cap", "%d on our list", "They close when the national draft starts.",
        "\"We delisted %s.\"", "\"%s signed with us.\"", "Undo it any time before the national draft starts.",
        "We have %s to spend on the football year. It resets next off-season. Nothing carries over.",
        "\"%s spent  ·  %s left\"", "off our budget this year.", "\"Fully funded.\"", "We get a draft pick %s for losing %s to %s.",
        "Leave one of our best 23 unsigned and he tests free agency. Our offer stands at his asking price. Rivals can beat it.",
        "Re-signed for %d more seasons at %s", "Talks broke down. He'll test free agency", "\"Our whole list\"",
        "He went around again once already. This time he's going.",
        "He leaves our list and becomes a free agent. We get no draft pick if he signs elsewhere.",
        "Our senior list is full at %d. Release a player first.", "\"After our offer: \"",
        "Rivals see our offer and can answer it once. Our second offer is final.",
        "Our next offer is final. Rivals answer, then he decides.", "Talks broke down. He'll look elsewhere",
        "\"We give\"", "\"We get\"", "Nothing yet. Add from our list below.", "Add what we want back. Or put him on the trade table.",
        "Add what we'd give. Or ask their price.", "\"Our list\"", "\"Offers for our players\"",
    ], ["\"Payroll", "list %d\"", "\"You delisted", "signed with you.\"", "\"You can undo", "to allocate for", "bank balance to hoard",
        "%s allocated", "\"Maximum funding", "\"Compensation:", "Leave one of your best 23", "\"Re-signed:", "\"Talks broke down:",
        "\"Whole list\"", "already: this time", "leave your list", "\"Your senior list", "\"After your offer", "once you make it",
        "\"Your next offer", "\"You give\"", "\"You get\"", "from your list below", "what you want back", "what you'd give",
        "\"Your list\"", "Offers for your players"]],
    "scripts/sim/Contracts.gd": [[
        "His opinion of you: %d out of 100. %d%% he won't re-sign with us.",
        "%s won't re-sign with us. His opinion of you: %d out of 100.",
        "He won't re-sign with us. His opinion of you: %d out of 100.",
        "Won't re-sign with us. His opinion of you: %d out of 100",
        "He's fighting for a list spot. He'll take less.", "He knows his worth. He won't take less.",
        "For %s or more, he'd sign for %s a season. That is %s under his ask.",
        "Offer under %s and he's insulted. It uses up %d of our %d offers. His morale drops %d%%.",
        "He wants senior football. He wouldn't make our best 23.", "\"The most money.\"",
        "Prefers %s offer. They are pushing to win now.", "Besides salary, he counts a best-23 spot as %s a season.",
        "\"he signs with us if ours is still worth the most to him", "no other club has offered, so he signs with us.",
        "%s a season on our cap for %d season%s. %s in all",
    ], ["/100.\"", "re-sign with you", "\"Won't re-sign:", "and will take less", "and won't take less", "under his ask, for",
        "of your %d offers", "make your best 23", "\"Best financial offer", "offer: they are", "(a bench spot",
        "\"he signs with you", "on your cap for"]],
    "scripts/ui/DraftTradeSheet.gd": [[
        "The draft waits while we deal.", "\"We give\"", "\"We get\"", "Nothing yet. Add one of our picks below.",
        "Nothing yet. Add one of their picks below.", "\"Our picks\"", "\"Offers for our pick\"",
    ], ["while you deal", "\"You give\"", "\"You get\"", "\"Nothing yet:", "\"Your picks\"", "Offers for your pick"]],
    "scripts/ui/StaffScene.gd": [[
        "\"Our club\"", "You broke %s to him. Our offers are %d%% less likely to land",
    ], ["\"Your club\"", "your offers weigh"]],
    "scripts/ui/FirstVisitIntro.gd": [[
        "\"Our staff\"", "Between the Grand Final and the draft, we rebuild the list.",
        "Keep the players we want first. Then fill the gaps.", "he's insulted. It counts as two failed offers and costs morale.",
        "Choose a club. Put players or picks on each side.", "To buy, add one of theirs alone and Ask their price.",
        "Contenders want help now. Rebuilders want youth and picks.",
        "Tonight only picks change hands, from this draft and the next two.",
        "When a club bids for our pick", "The draft waits while we deal. Tap Back to the draft when done.",
    ], ["\"Your staff\"", "draft you rebuild:", "players you want to keep", "insulted: it counts", "Want one of theirs?",
        "help now; rebuilders", "change hands: this draft", "bids for your pick", "your own deal", "this sheet is open"]],
    "scripts/state/GameState.gd": [[
        "%s out of contract. %s of them in our best 22.", "%s out of contract. None of them in our best 22.",
        "Our best six average %d years old.", "\"Behind, but \"",
    ], ["of them in your best 22", "\"Your best six average", "Behind, though:"]],
}

## Every pinned pass: (file, the pass, its rewritten lines, the lines they replaced).
PASSES = [(HUB, "copy voice pass 2, hub", HUB_NEW, HUB_OLD)] + [
    (path, "copy voice pass 5, team and coaching", v[0], v[1]) for path, v in TEAM_PASS.items()] + [
    (TRAINING, "copy voice pass 6, training", TRAINING_NEW, TRAINING_OLD)] + [
    (path, "copy voice pass 8, contracts and trades", v[0], v[1]) for path, v in CONTRACTS_PASS.items()]

LITERAL = re.compile(r'"([^"\n]*)"')

## The gates pass (copy voice pass 1): per file, the rewritten lines and the lines they replaced.
## One effect a line on the call cards (style guide 5.1): a gate's second effect starts its own line
## (a GDScript "\n"); the break sheet runs them on one line, parted by " · " (MatchScene._break_line).
GATES_PASS = {
    "scripts/sim/GateOdds.gd": [[
        "our shots %s more accurate\\nOur kicks gain %s more ground", "Their pressure bites %s less",
        "we get a %s better chance at every stoppage", "%s less pressure in our back third",
        "\\n(%s for a list that suits it)", "while we're behind\\nNothing when level or in front",
        "On top of a High Press, %s more", "With %s on him, about %d, until we call it off",
        "none: we have no midfielder on the ground to go to him", "our midfielders play their own game",
        "Skip plays the match on the plan we took in. No tag, no talk.", "\\nFor about %d minutes",
        "Anyone else, about %d", "our share of the ball doesn't grow",
    ], ["your shots", "your back third", "while you are behind", "until you call it off", "you have no midfielder",
        "your midfielders", "plan you took in", ", for about %d minutes", "(%s on top of a High Press)",
        "(never above %s)", "(%d for anyone else)", "the side's ball"]],
    "scripts/sim/MatchSim.gd": [[
        "He kicks these most days", "one of our best kicks for goal", "Stack the centre bounce",
        "\"Centre bounce · %s %s\"", "Their midfielder is hurting us on the scoreboard.", "Back our defenders",
        "Tag on. We can call it off at the break.", "Our stars stay on until they are cooked.",
    ], ["He should kick it", "one of your best kicks", "Stack the stoppage", "Centre ball-up - ",
        "hurting you on the scoreboard", "Back your defenders", "You can call it off at the break", "your stars"]],
    "scripts/sim/CoachReport.gd": [[
        "A lift at the contest while we're chasing the game.", "It leans on our ball-winners and ruck.",
        "It asks nothing special of our list.", "We gain less ground.", "A plan of our own",
    ], ["while you are chasing", "does nothing for you", "Leans on your", "of your list", "you are a little exposed",
        "Your own plan: the strength"]],
    "scripts/ui/MatchScene.gd": [["\" · \".join(parts)"], []],
}
PASSES += [(path, "copy voice pass 1, gates", v[0], v[1]) for path, v in GATES_PASS.items()]


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
