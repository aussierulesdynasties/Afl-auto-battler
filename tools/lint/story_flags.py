"""Every story flag a choice sets is read: by a follow-up's needs, a subject or choice condition
(flag / no_flag), or the game's code (story_flag_set(holder, "name")). A flag nothing reads is a
choice whose promised consequence never comes. Moved from test_story _test_no_dead_story_flags
on 2026-11-12, rule for rule. The deck is StoryDeck.all(): data/stories/<category>.json for each
StoryDeck.CATEGORIES, plus data/stories/international.json.
"""
import json
import re

from common import Finding, gd_const_strings, gd_files, read

STORY_DECK = "scripts/sim/StoryDeck.gd"
INTERNATIONAL = "data/stories/international.json"
CODE_READ = re.compile(r'story_flag_set\([^,()]+,\s*"([a-z_]+)"')


def code_flag_names(text):
    return CODE_READ.findall(text)


def code_flag_reads(root, d="scripts"):
    out = []
    for path in gd_files(root, d):
        out += code_flag_names(read(root, path))
    return out


def deck_files(root):
    cats = gd_const_strings(read(root, STORY_DECK), "CATEGORIES")
    return ["data/stories/%s.json" % c for c in cats] + [INTERNATIONAL]


def flag_reads(v, out):
    if isinstance(v, dict):
        for k in v:
            if k in ("flag", "no_flag") and isinstance(v[k], str):
                out.add(v[k])
            else:
                flag_reads(v[k], out)
    elif isinstance(v, list):
        for x in v:
            flag_reads(x, out)


def dead_flags(deck, code_reads):
    """({flag: "card/choice"} for every flag a choice sets, [dead flags with their setter])."""
    set_by, reads = {}, set()
    for t in deck:
        for o in t.get("choices", []):
            for e in o.get("effects", []):
                if str(e.get("op", "")) == "flag":
                    set_by[str(e["name"])] = "%s/%s" % (t["id"], o["key"])
            flag_reads(o.get("when", {}), reads)
        rest = {k: v for k, v in t.items() if k != "choices"}
        flag_reads(rest, reads)
    reads |= set(code_reads)
    return set_by, ["%s (set by %s)" % (f, set_by[f]) for f in set_by if f not in reads]


def check(root):
    out = []
    code = code_flag_reads(root)
    if "farewell_told" not in code:
        out.append(Finding("scripts", 0, "story-flags", "the code scan no longer finds a flag the code reads by name (farewell_told)"))
    deck, where = [], {}
    for path in deck_files(root):
        text = read(root, path)
        if not text:
            continue  # StoryDeck.load_dir skips a missing category file too
        try:
            cards = json.loads(text)
        except ValueError as e:
            out.append(Finding(path, 0, "story-flags", "does not parse as JSON: %s" % e))
            continue
        for t in cards if isinstance(cards, list) else []:
            if isinstance(t, dict):
                deck.append(t)
                where[str(t.get("id", ""))] = (path, text)
    set_by, dead = dead_flags(deck, code)
    if len(set_by) < 9:
        out.append(Finding("data/stories", 0, "story-flags", "the deck sets too few story flags to be read (%d)" % len(set_by)))
    for d in dead:
        card = set_by[d.split(" ", 1)[0]].split("/", 1)[0]
        path, text = where.get(card, ("data/stories", ""))
        i = text.find('"%s"' % d.split(" ", 1)[0])
        out.append(Finding(path, text.count("\n", 0, i) + 1 if i >= 0 else 0, "story-flags",
                           "story flag %s is never read: no follow-up's needs, no flag/no_flag condition, and no "
                           "story_flag_set(..., \"name\") in scripts/" % d))
    return out


CHECKS = [check]
