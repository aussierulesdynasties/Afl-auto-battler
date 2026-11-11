"""Screen source rules, moved from the Godot suites on 2026-11-12, rule for rule:

- font-size-one-place  (text_size _test_one_place): only UiKit sets a font size on a control.
- colour-cue           (text_size _test_colour_has_words): where only GOOD/BAD colour would carry
                        a state, a word, mark or number says it too (P-10); each line is listed.
- type-role            (career_ui _test_type_roles): every literal text size is a UiKit role.
- raw-club-ink         (matchday _test_club_ink_all, part 2): no screen paints a name label in a
                        raw club ink (UiKit.club_name_colour).
- green-decoration     (test_matchday _test_no_green_decoration): green is a state, not an accent.
"""
import re

from common import Finding, gd_const_ints, gd_files, is_comment, read

UIKIT = "scripts/ui/UiKit.gd"


def check_font_size_one_place(root):
    """Only UiKit sets a font size on a control; everything else asks it, so the text size
    reaches every word."""
    files = gd_files(root, "scripts")
    out = []
    if len(files) <= 50:
        out.append(Finding("scripts", 0, "font-size-one-place", "the scripts are not all read (%d)" % len(files)))
    for path in files:
        if path.endswith("/ui/UiKit.gd"):
            continue
        for n, line in enumerate(read(root, path).split("\n"), 1):
            if "add_theme_font_size_override" in line:
                out.append(Finding(path, n, "font-size-one-place",
                                   "a font size set outside UiKit: ask UiKit for the size (UiKit.set_font_size) instead"))
    return out


## Where only GOOD/BAD (or win/loss) colour would carry a state, a word, mark or number says it
## too (P-10). Each such line in the screens names its second cue here: [part of the line, the
## cue that says the same thing, how many lines it is on]. The count pins each part to its
## lines, so a new line that happens to contain one still has to be read and counted.
COLOUR_CUES = {
    "CaptaincySheet.gd": [["UiKit.BAD if off_bad", "the reason he can't lead, in words", 1]],
    "ClubPage.gd": [["UiKit.GOOD if us > them", "Won / Lost / Drew", 1]],
    "CoachingScene.gd": [
        ["part[1] == \"hot\"", "the heading: In good form / In poor form", 1],
        ["state in [\"Very secure\", \"Secure\"]", "the job security word", 1],
        ["UiKit.TEXT if state == \"Stable\"", "the job security word", 1]],
    "DraftScene.gd": [
        ["Traits.is_bad(str(t))", "the weakness mark", 1],
        ["\"On your list\"", "On your list, pick N", 1],
        ["int(st[\"short\"]) > 0", "the need word (short of ...)", 1],
        ["_draft.is_valid()", "the status line in words", 1]],
    "DraftSpotsSheet.gd": [["str(line[2]) == \"bad\"", "the line says who will pass", 1]],
    "DraftTradeSheet.gd": [["bool(verdict[\"ok\"])", "the club's reason in words", 1]],
    "HubScene.gd": [
        ["\"You have retired\" if retired", "You have retired / You have been sacked", 1],
        ["\"own_injury\"", "the note names the injury", 1],
        ["UiKit.GOOD if done", "Done / To do", 1],
        ["ch == \"W\"", "the W / L / D letters", 1],
        ["return UiKit.GOOD", "the form line's words", 1],
        ["return UiKit.BAD", "the form line's words", 1],
        ["margin_colour(won)", "Won by / Lost by / Drew", 2],
        ["UiKit.GOOD if won else UiKit.BAD", "Challenge won / lost; Cleared or the ban in words", 2]],
    "ListScene.gd": [
        ["concussion_text(p), UiKit.BAD", "the concussion in words", 1],
        ["\"Out %s\"", "Out N weeks", 1],
        ["\"Unhappy\"", "Unhappy", 1]],
    "MatchScene.gd": [
        ["pts > 0", "the signed +/- points", 1],
        ["bool(f[2])", "the legs word", 1],
        ["tone == \"good\"", "the goal row names the club", 1],
        ["margin_colour(winner == me)", "Won by / Lost by", 1]],
    "OffseasonScene.gd": [
        ["room >= 0 else UiKit.BAD", "cap room / over the cap by", 1],
        ["talk[\"stays\"]", "his reason in words", 1],
        ["terms[\"refuse\"]", "his reason in words", 1],
        ["room_after >= 0 else UiKit.BAD", "none, over the cap", 1],
        ["verdict[\"ok\"]", "the club's reason in words", 1]],
    "OptionsSheet.gd": [["UiKit.BAD if bad", "the status line in words", 1]],
    "PlayerSheet.gd": [
        ["weeks > 0", "Out for N weeks", 1],
        ["Traits.is_bad(str(t))", "the weakness mark", 1],
        ["return UiKit.GOOD", "the rating's number", 1],
        ["return UiKit.BAD", "the rating's number", 1]],
    "SeasonReviewScene.gd": [
        ["mine_won", "the result in words", 1],
        ["\"met\"", "met / missed", 1],
        ["col = UiKit.GOOD", "the W / L letters", 1],
        ["col = UiKit.BAD", "the W / L letters", 1]],
    "TeamBuilder.gd": [
        ["start_note != \"\"", "the note in words", 1],
        ["Workload.NEEDS_BREAK", "the workload word", 1],
        ["Ratings.available(p)", "why he is out, in words", 1]],
    "TrainingScene.gd": [
        ["rise.size() > 0", "the rise mark and its words", 2],
        ["Traits.is_bad(trait_keys[0])", "the weakness mark", 1],
        ["\"Injured %d wk%s\"", "Injured N wks", 1],
        ["useful else UiKit.BAD", "Does little for a ...", 1],
        ["return UiKit.GOOD", "the rating's number", 1],
        ["return UiKit.BAD", "the rating's number", 1]],
    "TraitLink.gd": [["Traits.is_bad(key)", "the sheet says Weakness", 1]],
    "UiKit.gd": [
        ["BAD if danger", "the button's words", 1],
        ["BAD if Traits.is_bad(t)", "the weakness mark", 1],
        ["func margin_colour(", "callers write Won by / Lost by", 1],
        ["GOOD if win else BAD", "callers write Won by / Lost by", 1]],
    "WeekPreview.gd": [
        ["UiKit.BAD if bad", "the note in words", 2],
        ["lit[Traits.label", "Your side has: ...", 1]],
}
## A colour chosen by a state: "GOOD if", "else BAD", "return GOOD", "= BAD", a margin colour,
## or handed back beside its words as [text, GOOD].
COLOUR_ONLY = re.compile(r"\b(GOOD|BAD)\s+if\b|\belse\s+(UiKit\.)?(GOOD|BAD)\b|margin_colour\(|return\s+(UiKit\.)?(GOOD|BAD)\b"
                         r"|=\s*(UiKit\.)?(GOOD|BAD)\s*$|\b(GOOD|BAD)\s*\]")


def check_colour_cues(root, cues=None):
    cues = COLOUR_CUES if cues is None else cues
    out = []
    counted = {}
    found = 0
    for path in gd_files(root, "scripts/ui"):
        file = path.rsplit("/", 1)[-1]
        for n, line in enumerate(read(root, path).split("\n"), 1):
            if is_comment(line) or not COLOUR_ONLY.search(line):
                continue
            found += 1
            for cue in cues.get(file, []):
                if cue[0] in line:
                    counted[(file, cue[0])] = counted.get((file, cue[0]), 0) + 1
                    break
            else:
                out.append(Finding(path, n, "colour-cue",
                                   "a state shown by colour alone: add its word or mark, then list the line in "
                                   "COLOUR_CUES (tools/lint/screens.py): %s" % line.strip()))
    if found <= 30:
        out.append(Finding("scripts/ui", 0, "colour-cue", "the screens' state colours are not all read (%d)" % found))
    for file in cues:
        for cue in cues[file]:
            n = counted.get((file, cue[0]), 0)
            if n != cue[2]:
                out.append(Finding("scripts/ui/" + file, 0, "colour-cue",
                                   "%s is on %d lines, listed for %d in COLOUR_CUES: read each line, then fix its "
                                   "count or drop it" % (cue[0], n, cue[2])))
    return out


TEXT_CALL = re.compile(r"UiKit\.(lbl|line|ellipsis|figure|heading|btn|name_label|set_font_size)\(")
SIZE_ARG = re.compile(r"[,(]\s*(\d{1,2})\s*[,)]")
SIZE_OVERRIDE = re.compile(r'font_size", (\d{1,2})')


def check_type_roles(root):
    """Type roles (docs/VISUAL_STYLE_GUIDE.md §2.3): a screen never sets a font size that is not
    one of UiKit's roles (UiKit.SIZES)."""
    sizes = gd_const_ints(read(root, UIKIT), "SIZES")
    files = gd_files(root, "scripts/ui")
    out = []
    if len(files) <= 20:
        out.append(Finding("scripts/ui", 0, "type-role", "the type-role check did not see the screens (%d files)" % len(files)))
    for path in files:
        if path.endswith("UiKit.gd"):
            continue
        for n, line in enumerate(read(root, path).split("\n"), 1):
            if is_comment(line):
                continue
            hits = []
            if TEXT_CALL.search(line):
                hits += [int(m.group(1)) for m in SIZE_ARG.finditer(line)]
            hits += [int(m.group(1)) for m in SIZE_OVERRIDE.finditer(line)]
            for h in hits:
                if h >= 6 and h not in sizes:
                    out.append(Finding(path, n, "type-role", "text size %d is not a UiKit role (UiKit.SIZES: %s)"
                                       % (h, ", ".join(str(s) for s in sizes))))
    return out


def check_raw_club_ink(root):
    """No screen script hands a raw club ink to a name label or its font colour (found
    2026-10-18: a Melbourne name read as the primary-action red)."""
    out = []
    for path in gd_files(root, "scripts/ui"):
        for n, ln in enumerate(read(root, path).split("\n"), 1):
            t = ln.strip()
            if t.startswith("#"):
                continue
            if (("lbl(" in t or "line(" in t or "ellipsis(" in t or "font_color" in t)
                    and ("UiKit.club_ink(" in t or "UiKit.club_ink_second(" in t)
                    and "club_name_colour(" not in t):
                out.append(Finding(path, n, "raw-club-ink",
                                   "a name label painted in a raw club ink: wrap it in UiKit.club_name_colour(...)"))
    return out


def check_green_decoration(root):
    """Green is a state (won, met, rising), not the game's accent: no screen paints a selection
    or a highlight with a green surface (#263025). Top-level scripts/ui only, as the suite read."""
    out = []
    for path in gd_files(root, "scripts/ui", recursive=False):
        text = read(root, path)
        for n, ln in enumerate(text.split("\n"), 1):
            if "263025" in ln:
                out.append(Finding(path, n, "green-decoration", "a green highlight surface (263025) in the UI"))
    return out


CHECKS = [check_font_size_one_place, check_colour_cues, check_type_roles, check_raw_club_ink, check_green_decoration]
