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
| autoload-reach | autoload_reach.py | No script whose extends chain reaches SceneTree (runner, harness) names, at compile time, a class whose chain (names, single- or double-quoted preloads, `extends "res://..."`) reaches an autoload: under `godot --script` it fails to compile and Godot hangs to the time limit. `load()` it inside `_run()`; a `var` of the same name shadows the class only in its own function. | new (StoryDeck, ClubForge and #978 breaks) |
| copy-voice | copy_voice.py | The banned words (`scripts/core/CopyRules.gd` WORDS) in story cards, tale banks and UI/sim/state string literals, at the exact ALLOW counts. | copy_rules `_test_sources` |
| copy-pass | copy_voice.py | Each copy voice pass keeps its rewritten lines and its old ones stay gone (PASSES: hub, team and coaching, training). | copy_rules `_test_hub_pass`, `_test_team_pass`, `_test_training_pass` |
| no-click | copy_voice.py | Phone first: no copy line (story cards, tale banks, UI/sim/state string literals) says "click"; it says "tap". | copy_rules `_test_no_click` |
| font-size-one-place | screens.py | No `add_theme_font_size_override` outside UiKit. | text_size `_test_one_place` |
| colour-cue | screens.py | A state colour (GOOD/BAD) always has a word or mark too (P-10); every such line is listed in COLOUR_CUES at its exact count. | text_size `_test_colour_has_words` |
| type-role | screens.py | Every literal text size on a screen is in `UiKit.SIZES`. | career_ui `_test_type_roles` |
| raw-club-ink | screens.py | No name label painted in a raw club ink (wrap in `UiKit.club_name_colour`). | matchday `_test_club_ink_all` part 2 |
| green-decoration | screens.py | No green highlight surface (263025) in `scripts/ui`. | test_matchday `_test_no_green_decoration` |
| boundaries | boundaries.py | Sim/state never read coaches, family ties or old club lines; nothing opens the old Culture sheet. | test_coaches `_test_no_effects_yet`, family, roles, matchup |
| export-presets | boundaries.py | Web phone keyboard on; Android save backup on. | keyboard `_test_preset`, career_ui |
| no-import-sidecars | boundaries.py | `captures/` and `docs/` keep a `.gdignore`, and no `*.import` sidecar is tracked under them (they conflicted in merges for no reason). | new (2026-11-12, CI conflicts) |
| csv-kept | boundaries.py | Every game CSV has a sidecar saying `importer="keep"`: otherwise Godot imports it as a translation, the export leaves it out, and the threaded import crashed CI (signal 11). | new (2026-11-14, CI crash) |
| story-flags | story_flags.py | Every story flag a choice sets is read by a card or by `story_flag_set(..., "name")`. | test_story `_test_no_dead_story_flags` |
| gdlint | gdlint_gate.py, gdlintrc | gdtoolkit's linter (naming, unused arguments, whitespace) against `gdlint_baseline.txt`. | new |

Each rule keeps its table (ALLOW, PASSES, COLOUR_CUES, BANNED) in its own file; edit
the table in the same PR as the line it covers, as before. What stays in Godot: anything that
needs the engine (CopyRules' own unit tests in clublink, contrast maths, image and audio
checks, StoryDeck.validate, ProjectSettings, taps), and the compile preflight
(`tools/ci_preflight_compile.sh`), which remains the ground truth for compiling.

## gdlint baseline

`gdlint_baseline.txt` lists the known problems (`count rule path`): 71 on 2026-11-12, unused
arguments and naming slips. A file may keep up to its count of each rule; one more fails.

A parse error is never baselined: gdtoolkit skips a file it cannot parse, so one baselined
parse error would exempt the whole file. Every tracked .gd parses since 2026-11-12. gdtoolkit
4.5.0 lags Godot on four legal forms; write them the way it reads:
a line break inside a `"..."` string (write `\n`), `set` or `get` as a variable name (rename),
`x == not y` (write `x == (not y)`), and a one-line lambda with an `if` body (put the body on
its own lines). When you fix some, the run notes the baseline can
shrink; rewrite it with `python3 -I tools/lint/lint.py --only gdlint --write-baseline`.
Never raise a count by hand to pass: fix the line, or rename it to match the rule.

## Adding a rule

Write `check(root) -> [Finding]` in a module here, register it in `lint.py` RULES, and add a
test to `test_lint.py` that breaks the rule in a throwaway repo and asserts the file and line.
Standard library only; run with `python3 -I`.
