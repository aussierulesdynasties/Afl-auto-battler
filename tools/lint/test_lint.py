"""Tests for the static lints themselves: each rule bites on a made-up break and names the file
and line, and passes the clean form. Run: python3 -I tools/lint/test_lint.py
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import autoload_reach  # noqa: E402
import boundaries  # noqa: E402
import copy_voice  # noqa: E402
import gdlint_gate  # noqa: E402
import screens  # noqa: E402
import story_flags  # noqa: E402
from common import ROOT, gd_const_ints, gd_const_strings, read  # noqa: E402

COPY_RULES_GD = '''class_name CopyRules
const WORDS := [
\t"should", "recommend", "recommended", "need to", "auto-pick", "best choice", "starters",
]
'''


class Repo(unittest.TestCase):
    """A throwaway repo: write(path, text) and the rule runs over it."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="lint_")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def write(self, rel, text):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    @staticmethod
    def at(found, rule=None):
        """'path:line' of each finding with a line (the per-line hits), optionally one rule."""
        return ["%s:%d" % (f.path, f.line) for f in found if f.line and (rule is None or f.rule == rule)]


class CopyVoice(Repo):
    def setUp(self):
        super().setUp()
        self.write("scripts/core/CopyRules.gd", COPY_RULES_GD)
        self.rx = copy_voice.words_re(gd_const_strings(COPY_RULES_GD, "WORDS"))

    def test_words_match_copy_rules(self):
        w = lambda s: copy_voice.words_in(self.rx, s)  # noqa: E731
        self.assertEqual(w("We should press higher"), ["should"])
        self.assertEqual(w("Shoulder: two weeks"), [])
        self.assertEqual(w("We RECOMMENDED it"), ["recommended"])
        self.assertEqual(w("Auto-pick names him"), ["auto-pick"])
        self.assertEqual(w("The best  choice here"), ["best choice"])
        self.assertEqual(w("Best 22 and the Fast Starters"), ["starters"])

    def test_a_banned_word_fails_with_file_and_line(self):
        self.write("scripts/ui/Screen.gd", 'func f():\n\t# "we should" in a comment is fine\n\treturn "We should kick it"\n')
        self.write("data/tales/career.json", '{"a": ["Fine words here"]}')
        found = copy_voice.check(self.root, allow={}, tales=["data/tales/career.json"])
        self.assertEqual(self.at(found), ["scripts/ui/Screen.gd:3"])
        self.assertIn("1 banned words (allowed 0", found[0].message)

    def test_allow_is_exact_both_ways(self):
        self.write("scripts/ui/Screen.gd", 'var a = "We should kick it"\n')
        self.assertEqual(copy_voice.check(self.root, allow={"scripts/ui/Screen.gd": [1, "should", "x"]}, tales=[]), [])
        found = copy_voice.check(self.root, allow={"scripts/ui/Screen.gd": [1, "should", "x"],
                                                   "scripts/ui/Gone.gd": [1, "should", "y"]}, tales=[])
        self.assertEqual([f.message for f in found], ["is clean now: drop it from ALLOW in tools/lint/copy_voice.py"])

    def test_a_story_card_and_a_tale_bank_are_read(self):
        self.write("data/stories/media.json", '[\n  {"id": "a",\n   "text": "Pundits say you should"}\n]\n')
        self.write("data/tales/season.json", '{"angles": {"surge": {"slots": ["run"], "coach": ["We should have won our last {run} games."]}}}')
        found = copy_voice.check(self.root, allow={}, tales=["data/tales/season.json"])
        self.assertEqual(sorted(self.at(found)), ["data/stories/media.json:3", "data/tales/season.json:1"])

    def test_a_missing_tale_bank_fails_by_name(self):
        found = copy_voice.check(self.root, allow={}, tales=["data/tales/career.json"])
        self.assertEqual([f.path for f in found], ["data/tales/career.json"])

    def test_hub_pins(self):
        self.write("scripts/ui/HubScene.gd", 'var a = "Our week"\nvar b = "Begin season"\n')
        found = copy_voice.check_passes(self.root, [(copy_voice.HUB, "copy voice pass 2, hub", ["Our week", "Start the season"], ["Begin season"])])
        self.assertEqual([f.text() for f in found], [
            "scripts/ui/HubScene.gd: [copy-pass] no longer says: Start the season (copy voice pass 2, hub pinned it)",
            "scripts/ui/HubScene.gd:2: [copy-pass] says an old line again: Begin season (copy voice pass 2, hub)"])


class Screens(Repo):
    def test_font_size_outside_uikit(self):
        self.write("scripts/ui/UiKit.gd", "func f(c):\n\tc.add_theme_font_size_override('font_size', 13)\n")
        self.write("scripts/ui/Screen.gd", "func f(c):\n\tpass\n\tc.add_theme_font_size_override('font_size', 13)\n")
        self.assertEqual(self.at(screens.check_font_size_one_place(self.root)), ["scripts/ui/Screen.gd:3"])

    def test_colour_alone_and_count(self):
        self.write("scripts/ui/Card.gd", "func f(won):\n\tvar c = UiKit.GOOD if won else UiKit.BAD\n"
                   "\t# return UiKit.GOOD in a comment\n\treturn UiKit.BAD\n")
        found = screens.check_colour_cues(self.root, cues={"Card.gd": [["UiKit.GOOD if won", "Won / Lost", 1]]})
        self.assertEqual(self.at(found, "colour-cue"), ["scripts/ui/Card.gd:4"])
        found = screens.check_colour_cues(self.root, cues={"Card.gd": [["UiKit.GOOD if won", "W", 2], ["return UiKit.BAD", "x", 1]]})
        self.assertEqual([f.message for f in found if f.path.endswith("Card.gd")],
                         ["UiKit.GOOD if won is on 1 lines, listed for 2 in COLOUR_CUES: read each line, then fix its count or drop it"])

    def test_type_roles(self):
        self.write("scripts/ui/UiKit.gd", "const BODY := 15\nconst SIZES := [BODY, 20]\n")
        self.write("scripts/ui/Screen.gd", 'var a = UiKit.lbl("x", 15)\nvar b = UiKit.lbl("x", 17)\n'
                   '# UiKit.lbl("x", 17)\nc.add_theme_font_size_override("font_size", 19)\n')
        self.assertEqual(gd_const_ints(read(self.root, "scripts/ui/UiKit.gd"), "SIZES"), [15, 20])
        self.assertEqual(self.at(screens.check_type_roles(self.root), "type-role"),
                         ["scripts/ui/Screen.gd:2", "scripts/ui/Screen.gd:4"])

    def test_raw_club_ink(self):
        self.write("scripts/ui/A.gd", "var a = UiKit.lbl(n, 16, UiKit.club_name_colour(UiKit.club_ink(c)))\n"
                   "var b = UiKit.lbl(n, 16, UiKit.club_ink(c))\n")
        self.assertEqual(self.at(screens.check_raw_club_ink(self.root)), ["scripts/ui/A.gd:2"])

    def test_green_decoration(self):
        self.write("scripts/ui/A.gd", 'var a = Color("1a1a1a")\nvar b = Color("263025")\n')
        self.assertEqual(self.at(screens.check_green_decoration(self.root)), ["scripts/ui/A.gd:2"])


class Boundaries(Repo):
    def test_banned_names(self):
        self.write("scripts/sim/MatchSim.gd", "func f():\n\tOldClubLines.line()\n")
        found = boundaries.check(self.root, banned=[("r", ["scripts/sim/MatchSim.gd"], ["OldClubLines"], "why"),
                                                    ("s", [("scripts/sim", False)], ["PlayerRelations"], "why")])
        self.assertEqual([f.text() for f in found], ["scripts/sim/MatchSim.gd:2: [r] why: names OldClubLines"])

    def test_a_missing_file_fails(self):
        found = boundaries.check(self.root, banned=[("r", ["scripts/sim/Gone.gd"], ["X"], "why")])
        self.assertEqual([f.path for f in found], ["scripts/sim/Gone.gd"])

    def test_presets(self):
        self.write("export_presets.cfg", "html/experimental_virtual_keyboard=false\nuser_data_backup/allow=true\n")
        self.assertEqual([f.rule for f in boundaries.check_presets(self.root)], ["web-keyboard", "web-keyboard"])
        self.write("export_presets.cfg", "html/experimental_virtual_keyboard=true\nuser_data_backup/allow=true\n")
        self.assertEqual(boundaries.check_presets(self.root), [])


class StoryFlags(Repo):
    def test_the_check_bites(self):
        self.assertEqual(story_flags.code_flag_names('if gs.story_flag_set(id, "t_code"):'), ["t_code"])
        deck = [
            {"id": "a", "choices": [{"key": "x", "effects": [{"op": "flag", "name": "t_unread"}, {"op": "flag", "name": "t_needs"},
                                                              {"op": "flag", "name": "t_choice"}, {"op": "flag", "name": "t_code"}]}]},
            {"id": "b", "needs": {"flag": "t_needs", "after": 1}, "choices": [{"key": "y", "when": {"no_flag": "t_choice"}, "effects": []}]}]
        self.assertEqual(story_flags.dead_flags(deck, ["t_code"])[1], ["t_unread (set by a/x)"])

    def test_a_dead_flag_names_its_card_file(self):
        self.write("scripts/sim/StoryDeck.gd", 'const CATEGORIES := ["media"]\n')
        self.write("scripts/sim/X.gd", 'if gs.story_flag_set(id, "farewell_told"):\n')
        self.write("data/stories/media.json", '[\n {"id": "a", "choices": [{"key": "x",\n  "effects": [{"op": "flag", "name": "t_dead"}]}]}\n]\n')
        found = story_flags.check(self.root)
        self.assertEqual(self.at(found), ["data/stories/media.json:3"])


class AutoloadReach(Repo):
    def setUp(self):
        super().setUp()
        self.write("project.godot", '[autoload]\n\nGameDB="*res://scripts/core/GameDB.gd"\n\n[display]\n')
        self.write("scripts/core/GameDB.gd", "extends Node\n")
        self.write("scripts/sim/Deck.gd", "class_name Deck\nstatic func all():\n\treturn GameDB.x\n")
        self.write("scripts/sim/Engine2.gd", "class_name Engine2\nstatic func f():\n\treturn Deck.all()\n")
        self.write("scripts/sim/Pure.gd", "class_name Pure\nstatic func f():\n\treturn 1\n")
        self.files = ["scripts/core/GameDB.gd", "scripts/sim/Deck.gd", "scripts/sim/Engine2.gd", "scripts/sim/Pure.gd"]

    def run_on(self, runner):
        self.write("tests/run_x_tests.gd", runner)
        return autoload_reach.check(self.root, files=self.files + ["tests/run_x_tests.gd"])

    def test_a_chain_to_an_autoload_is_named(self):
        found = self.run_on('extends SceneTree\n# Deck in a comment\nfunc _run():\n\tvar s = "Deck"\n\tEngine2.f()\n')
        self.assertEqual(self.at(found), ["tests/run_x_tests.gd:5"])
        self.assertIn("Engine2 -> Deck -> GameDB", found[0].message)

    def test_an_autoload_named_directly(self):
        self.assertEqual(self.at(self.run_on("extends SceneTree\nfunc _run():\n\tGameDB.x\n")), ["tests/run_x_tests.gd:3"])

    def test_a_preload_chain(self):
        found = self.run_on('extends SceneTree\nconst D := preload("res://scripts/sim/Deck.gd")\n')
        self.assertEqual(self.at(found), ["tests/run_x_tests.gd:2"])

    def test_load_by_path_and_shadowing_pass(self):
        self.assertEqual(self.run_on('extends SceneTree\nvar Deck\nfunc _run():\n\tDeck = load("res://scripts/sim/Deck.gd")\n'
                                     '\tPure.f()\n\tDeck.all()\n'), [])

    def test_a_string_over_a_line_break_hides_its_words(self):
        # Godot accepts a double-quoted string that runs over a line break (run_matchday_tests.gd);
        # its words are not names, and the lines after it keep their numbers.
        found = self.run_on('extends SceneTree\nfunc _run():\n\tprint("a\nDeck: " + str(load("res://x/Deck.gd")))\n'
                            '\t# "a quote in a comment\n\tEngine2.f()\n')
        self.assertEqual(self.at(found), ["tests/run_x_tests.gd:6"])

    def test_a_cycle_does_not_hide_a_later_runner(self):
        # Alpha names Beta and Gamma, Beta names Alpha, Gamma names GameDB. Walking from run_a caches
        # Beta's walk cut short at Alpha; run_b names Beta and must still be caught (2026-11-12 review).
        self.write("scripts/sim/Alpha.gd", "class_name Alpha\nstatic func f():\n\tBeta.f()\n\tGamma.f()\n")
        self.write("scripts/sim/Beta.gd", "class_name Beta\nstatic func f():\n\tAlpha.f()\n")
        self.write("scripts/sim/Gamma.gd", "class_name Gamma\nstatic func f():\n\tGameDB.x\n")
        self.write("tests/run_a_tests.gd", "extends SceneTree\nfunc _run():\n\tAlpha.f()\n")
        self.write("tests/run_b_tests.gd", "extends SceneTree\nfunc _run():\n\tBeta.f()\n")
        files = self.files + ["scripts/sim/Alpha.gd", "scripts/sim/Beta.gd", "scripts/sim/Gamma.gd",
                              "tests/run_a_tests.gd", "tests/run_b_tests.gd"]
        found = autoload_reach.check(self.root, files=files)
        self.assertEqual(self.at(found), ["tests/run_a_tests.gd:3", "tests/run_b_tests.gd:3"])

    def test_a_single_quoted_preload(self):
        found = self.run_on("extends SceneTree\nconst D := preload('res://scripts/sim/Deck.gd')\n")
        self.assertEqual(self.at(found), ["tests/run_x_tests.gd:2"])

    def test_a_class_extending_a_path_is_followed(self):
        self.write("scripts/sim/Child.gd", 'class_name Child\nextends "res://scripts/sim/Deck.gd"\n')
        self.files.append("scripts/sim/Child.gd")
        found = self.run_on("extends SceneTree\nfunc _run():\n\tChild.new()\n")
        self.assertEqual(self.at(found), ["tests/run_x_tests.gd:3"])
        self.assertIn("Child -> Deck.gd -> GameDB", found[0].message)

    def test_a_runner_whose_base_extends_scenetree(self):
        # A runner that extends a SceneTree base by path is started with --script too, and the base
        # it compiles names Deck.
        self.write("tests/base_runner.gd", "extends SceneTree\nfunc _go():\n\tpass\n")
        self.write("tests/deck_base.gd", "extends SceneTree\nfunc _go():\n\tDeck.all()\n")
        self.files += ["tests/base_runner.gd", "tests/deck_base.gd"]
        self.assertEqual(self.run_on("extends 'res://tests/base_runner.gd'\nfunc _run():\n\tEngine2.f()\n")[0].line, 3)
        found = self.run_on('extends "res://tests/deck_base.gd"\nfunc _run():\n\tpass\n')
        self.assertIn("tests/run_x_tests.gd:1", self.at(found))

    def test_a_local_shadows_only_its_own_function(self):
        found = self.run_on('extends SceneTree\nfunc _a():\n\tvar Deck = load("res://scripts/sim/Deck.gd")\n'
                            '\tDeck.all()\nfunc _b():\n\tDeck.all()\n')
        self.assertEqual(self.at(found), ["tests/run_x_tests.gd:6"])  # _b names it unshadowed
        self.assertEqual(len(found), 1)
        self.assertEqual(self.run_on('extends SceneTree\nfunc _a():\n\tvar Deck = load("res://scripts/sim/Deck.gd")\n'
                                     '\tDeck.all()\n'), [])

    def test_a_non_scenetree_script_may_name_anything(self):
        self.write("scripts/ui/Screen.gd", "extends Control\nfunc f():\n\tGameDB.x\n")
        self.assertEqual(autoload_reach.check(self.root, files=self.files + ["scripts/ui/Screen.gd"]), [])


class Gdlint(unittest.TestCase):
    OUT = ("../../scripts/sim/A.gd:167: Error: unused function argument 'seed' (unused-argument)\n"
           "../../scripts/sim/B.gd:\n\nNo terminal matches '\"' in the current parser context, at line 542 col 9\n\n"
           "\treturn \"%s\n               ^\nExpected one of: \n\t* LPAR\n"
           "../../scripts/sim/A.gd:170: Error: unused function argument 'year' (unused-argument)\n"
           "Failure: 3 problems found\n")

    def test_output_is_parsed(self):
        root = os.path.abspath(os.path.join(gdlint_gate.HERE, "..", ".."))
        found = gdlint_gate.parse(root, self.OUT)
        self.assertEqual([(f.path, f.line, f.rule) for f in found], [
            ("scripts/sim/A.gd", 167, "unused-argument"), ("scripts/sim/B.gd", 542, "parse-error"),
            ("scripts/sim/A.gd", 170, "unused-argument")])

    def test_the_gate_holds_the_baseline(self):
        root = os.path.abspath(os.path.join(gdlint_gate.HERE, "..", ".."))
        found = gdlint_gate.parse(root, self.OUT)
        files = ["scripts/sim/A.gd", "scripts/sim/B.gd"]
        base = {("scripts/sim/A.gd", "unused-argument"): 2}
        found = [f for f in found if f.rule != "parse-error"]
        self.assertEqual(gdlint_gate.gate(found, files, base), ([], []))
        base[("scripts/sim/A.gd", "unused-argument")] = 1
        new, _ = gdlint_gate.gate(found, files, base)
        self.assertEqual(["%s:%d %s" % (f.path, f.line, f.rule) for f in new],
                         ["scripts/sim/A.gd:167 gdlint/unused-argument", "scripts/sim/A.gd:170 gdlint/unused-argument"])
        base[("scripts/sim/A.gd", "unused-argument")] = 3
        self.assertEqual(len(gdlint_gate.gate(found, files, base)[1]), 1)  # a shrink note, not a failure

    def test_a_parse_error_always_fails_even_baselined(self):
        # A file gdtoolkit cannot parse is not linted at all, so a baseline of 1 parse-error would
        # exempt the whole file (GameState.gd was, until 2026-11-12).
        root = os.path.abspath(os.path.join(gdlint_gate.HERE, "..", ".."))
        found = gdlint_gate.parse(root, self.OUT)
        base = {("scripts/sim/A.gd", "unused-argument"): 2, ("scripts/sim/B.gd", "parse-error"): 1}
        new, _ = gdlint_gate.gate(found, ["scripts/sim/A.gd", "scripts/sim/B.gd"], base)
        self.assertEqual(["%s:%d %s" % (f.path, f.line, f.rule) for f in new], ["scripts/sim/B.gd:542 gdlint/parse-error"])
        self.assertIn("write \\n", new[0].message)


class TheRealTablesParse(unittest.TestCase):
    """The tables the lints read from the game's own source still parse."""

    def test_sources(self):
        self.assertIn("should", gd_const_strings(read(ROOT, "scripts/core/CopyRules.gd"), "WORDS"))
        self.assertGreater(len(gd_const_ints(read(ROOT, "scripts/ui/UiKit.gd"), "SIZES")), 5)
        self.assertGreater(len(story_flags.deck_files(ROOT)), 5)
        self.assertIn("GameDB", autoload_reach.autoload_names(ROOT))


if __name__ == "__main__":
    unittest.main(verbosity=1)
