# Static lints

Rules that read source text and need no Godot. They run first in CI (the Tests `lint` job),
fail in about a minute, and name the file, the line and the rule.

## Run them

```bash
python3 -I tools/lint/lint.py                         # every rule; gdlint on every tracked .gd
python3 -I tools/lint/lint.py --changed origin/main   # gdlint only on the .gd you changed
python3 -I tools/lint/lint.py --only copy-voice       # one rule (--list names them)
python3 -I tools/lint/test_lint.py                    # the lints' own tests
```

gdlint needs `pip install -r tools/lint/requirements.txt` (gdtoolkit 4.5.0). Without it the
other rules still run and gdlint is skipped with a note. `tools/run_tests.sh` runs all of this
with its dataset and harness checks; `--quick` and every suite run (CI shards, nightly.yml,
run_on_github.yml) run `autoload-reach` before any Godot starts.

A failure prints `path:line: [rule] message` (and a GitHub annotation on CI).

## The rules

| Rule | File | What it checks | Came from |
|---|---|---|---|
| autoload-reach | autoload_reach.py | No `extends SceneTree` script (runner, harness) names, at compile time, a class whose chain reaches an autoload: under `godot --script` it fails to compile and Godot hangs to the time limit. `load()` it inside `_run()`. | new (StoryDeck, ClubForge and #978 breaks) |
| copy-voice | copy_voice.py | The banned words (`scripts/core/CopyRules.gd` WORDS) in story cards, tale banks and UI/sim/state string literals, at the exact ALLOW counts. | copy_rules `_test_sources` |
| hub-copy | copy_voice.py | The hub's rewritten lines stay; the old ones stay gone. | copy_rules `_test_hub_pass` |
| font-size-one-place | screens.py | No `add_theme_font_size_override` outside UiKit. | text_size `_test_one_place` |
| colour-cue | screens.py | A state colour (GOOD/BAD) always has a word or mark too (P-10); every such line is listed in COLOUR_CUES at its exact count. | text_size `_test_colour_has_words` |
| type-role | screens.py | Every literal text size on a screen is in `UiKit.SIZES`. | career_ui `_test_type_roles` |
| raw-club-ink | screens.py | No name label painted in a raw club ink (wrap in `UiKit.club_name_colour`). | matchday `_test_club_ink_all` part 2 |
| green-decoration | screens.py | No green highlight surface (263025) in `scripts/ui`. | test_matchday `_test_no_green_decoration` |
| boundaries | boundaries.py | Sim/state never read coaches, family ties or old club lines; nothing opens the old Culture sheet. | test_coaches `_test_no_effects_yet`, family, roles, matchup |
| export-presets | boundaries.py | Web phone keyboard on; Android save backup on. | keyboard `_test_preset`, career_ui |
| story-flags | story_flags.py | Every story flag a choice sets is read by a card or by `story_flag_set(..., "name")`. | test_story `_test_no_dead_story_flags` |
| gdlint | gdlint_gate.py, gdlintrc | gdtoolkit's linter (naming, unused arguments, whitespace) against `gdlint_baseline.txt`. | new |

Each rule keeps its table (ALLOW, HUB_NEW/HUB_OLD, COLOUR_CUES, BANNED) in its own file; edit
the table in the same PR as the line it covers, as before. What stays in Godot: anything that
needs the engine (CopyRules' own unit tests in clublink, contrast maths, image and audio
checks, StoryDeck.validate, ProjectSettings, taps), and the compile preflight
(`tools/ci_preflight_compile.sh`), which remains the ground truth for compiling.

## gdlint baseline

`gdlint_baseline.txt` lists the problems known when the gate started (`count rule path`): 28
unused arguments, 34 naming slips, and 22 files gdtoolkit cannot parse though Godot can (a
newline inside a string, `set`/`get` as a variable name, `x == not y`). A file may keep up to
its count of each rule; one more fails. When you fix some, the run notes the baseline can
shrink; rewrite it with `python3 -I tools/lint/lint.py --only gdlint --write-baseline`.
Never raise a count by hand to pass: fix the line, or rename it to match the rule.

## Adding a rule

Write `check(root) -> [Finding]` in a module here, register it in `lint.py` RULES, and add a
test to `test_lint.py` that breaks the rule in a throwaway repo and asserts the file and line.
Standard library only; run with `python3 -I`.
