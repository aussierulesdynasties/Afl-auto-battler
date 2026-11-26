# AFL Auto-Battler: working rules

The design bible is read on demand (below). `docs/TODO.md` is the one list of work not done:
read it when you pick or close work, not otherwise (a brief that names your row is enough). Director rulings are in
`docs/DIRECTOR_BIBLE.md` (513 KB: search it, never read it whole). Must-read files stay under 60 KB (CI: `tools/check_doc_sizes.py`).

Godot 4 / GDScript. Run `tools/run_tests.sh` (or `tools/run_tests.sh draft_ui`
for one suite) before pushing. Hooks in `.claude/hooks/pr_guard.py` enforce the PR rules: they refuse a merge of a
conflicting PR, a merge of main that isn't needed, a second push within 20 min, and ending a turn
after a push with nothing set to wake you; each refusal names its override. In a cloud session they
install Godot and gdlint at start, so run the suites there too. MetaHuman files (and anything made from them) never go in this public
repo: they live in a private repo and `tools/epic_assets.sh fetch` copies them in (docs/EPIC_ASSETS.md).
Ground models (`assets/grounds/`) live there too: publish them with `tools/ground_assets.sh`, never `git add` (docs/GROUND_ASSETS.md).

## The design bible comes first (director, 2026-10-09)

[docs/DESIGN_BIBLE.md](docs/DESIGN_BIBLE.md) is read on demand (director, 2026-11-25), not
at session start. Read the sections that bear on the work (vision, the four pillars, the
principles, the coach, match day and the visual sim, the art standard, the feature test,
balance, what this game will not have) before you assess a feature, make a design or copy
call, touch the sim, art or a decision gate, or answer anything it may already rule on.
It is the ultimate truth for what this game is. Both Claude accounts and every
role work from it.

- **Authority.** Where this file, the roadmap or any other document disagrees
  with the bible, the bible wins: report the conflict and correct the other
  document. `docs/TODO.md` owns execution, status and order.
- **Nobody edits the bible without the director.** Each change needs the
  director's explicit consent for that change. Propose it; do not make it.
- **Assess before you build.** Before starting a feature, say in a line or two
  whether it deserves to exist against the bible's feature test and which intent
  it serves. The director's say is final.
- **What can affect the sim.** What the coach says or decides can affect the
  sim. How the club looks or sounds never does. Weather is the one exception
  (the condition affects play; its look does not).
- **Art is checked before the director sees it.** Inspect your own output first.
  Never ask for approval on work with a visible fault: skin through a jumper,
  broken anatomy, a bizarre animation, a ball that hovers or moves independently
  of the player using it, a ground that breaks AFL conventions.
- **Balance is the director's to call.** An agent may report that the numbers
  are close to real AFL. Balance is settled only when the director's own
  playtest also passes. Never declare it done.

## Project philosophy (permanent)

**Designed by a person, developed with AI, never designed by AI.** The director
supplies the vision, taste, AFL knowledge, priorities and final judgement.

- **Mobile first, portrait first.** An Android phone in portrait is the
  reference design; desktop is secondary. No hover-only information, thumb-sized
  targets, deliberate scrolling, natural Android Back.
- **Numbers belong at the decision gate (director, 2026-10-18).** Each option
  states its upside, its downside, the size and the odds, in football words, as
  percentages, and never which is better. Off the gate, show a number only when it
  helps the player understand or decide; no hidden diagnostics on the main
  surface, detail behind deliberate drill-downs.
- **Visual references are selective.** AFCM is not a visual aspiration. Preserve the established editorial design; clean screens must still expose the facts needed for the current choice. Read the focused chapters linked from [genre research](docs/GENRE_ENJOYMENT_RESEARCH.md); director decisions and scoped accepted extensions are recorded in roadmap §9.2.
- **No UI vomit.** One clear job per screen. If two elements answer the same
  question, keep the better one. Do not build UI just because data exists.
- **No generic AI-template design** (details below).
- **Natural AFL language.** Write what a coach, recruiter, commentator, player
  or supporter would actually say. No pseudo-football, engine terms or
  software-documentation prose.
- **Gameplay before analytics.** Revisit hidden simulation mechanics only when
  play exposes a real problem, a feature needs it, or the director asks.
- **Make the rules transparent; don't make the decision.** Show opponent
  facts, player identities and capabilities, and let every rule be looked up
  exactly (what a synergy needs, what a role does). Let the player decide the
  response: no "best choice" labels, suggested line-ups, recommendation
  prompts, optimal matchup hints or "one more X" checklists on the main
  surface - there may be several reasonable answers with trade-offs.
- **Every club gets it, and options are equal (director, 2026-11-09).** Every buff or cost the player's club gets, every rival club gets too. Options such as archetypes are equal, each with real positives and negatives, and none better on the scoreboard. Never ask the director either point: "stop asking stupid questions you know the answer to".
- **Every mode hosts the Club Forge (director, 2026-11-15).** "EVERY mode needs to be able to host our forge creations": every start, season, challenge and new mode offers your Forge prospect and your Forge club, and brings them into the career. A mode that cannot host them yet is a bug to fix, not a rule to write. `_test_forge_on_every_start` walks every start on the year step.
- **Questions only he can answer (director, 2026-11-09).** Before listing a decision for the director, search `docs/DIRECTOR_BIBLE.md`, `docs/TODO.md` and this file. Strike every question a ruling already answers and apply the ruling instead. Whoever shows him a list checks it first, including lists written by an agent.
- **Restraint is a feature.** A good idea is not automatically a good addition.
  Prefer the simplest thing that creates the football fantasy.
- **Challenge the director** when an idea conflicts with this philosophy, is
  poorly scoped or has a simpler alternative. Say so, then propose better.
- **A roadmap is context, not authorisation.** Do not start a roadmap item,
  branch, PR or follow-up until it is explicitly assigned. When an assigned
  task is done: stop, report, recommend the next step, wait.

## Verification (director, 2026-10-06, from the #291 assessment)

- **Real taps.** A UI flow is proven with a real tap at the control's position on screen, not only by calling its handler (`emit_signal("pressed")`): overlays and hit areas that block a finger only show up that way. New or changed touch flows get at least one real-tap check.
- **The right art loaded.** A capture or test of a vignette or figure proves the intended sheet or atlas loaded, not a fallback.
- **Change approach after repeated failure.** After two similar failed fixes of the same problem, stop patching: gather different evidence (a capture, a trace, a measurement) and rethink the approach before trying again.
- **Balance is measured locally (director, 2026-11-04).** Any balance-gated row, match-engine change or play-touching feature is screened with `tools/balance.sh match 1000` (paired: main vs the branch, `--a-root <main checkout> --b ""`; there are no feature switches, director 2026-11-06), about 85 s for 1,000 paired matches on 14 parallel Godot workers; the report marks each stat IN/NEAR/OUT of real AFL 2026 team rates and gives B-A with its standard error. Paste the table in the PR. Improve the harness (new modes, stats, references) instead of writing one-off probes; see tools/balance/README.md.

## Getting a PR merged (director, 2026-11-26)

CI is a shared pool of about 20 GitHub runners. A full Tests run needs up to 30 jobs, so every
extra push or PR makes every other PR wait. On 26 Nov PRs waited hours for runners while
the jobs themselves took about 30 min. Merges took days, and the director calls it the
number one development blocker.

- **Never end a turn with CI pending and nothing to wake you.** After you push, subscribe to the
  PR's activity (`subscribe_pr_activity`) or schedule a check-in (`send_later`); on a machine
  with a full `gh`, `gh pr checks <n> --watch` also works. A red check that sits for hours
  because nobody looked is the most common failure here.
- **A red check is the next job.** Read the failed job's log, fix it, push once. Do not start
  other work, open another PR or ask the director to merge while your PR is red.
- **Push once, not in drips.** Each push cancels the run in progress and goes to the back of the
  queue (45 cancelled PR runs on 26 Nov). Batch your commits locally and run the touched suites
  with `tools/run_tests.sh <suite>` before you push.
- **Respect the open PR cap (Director Bible 7.48): at most 3 ready PRs.** Over the cap, open
  yours as a draft (drafts skip the game tests) and mark it ready when a slot frees. Count
  the open PRs that are not drafts (GitHub MCP `list_pull_requests`, or `gh pr list`). The
  `PR cap` workflow enforces it: a PR over the cap goes back to draft and is released in turn.
- **Check for a conflict before you ask for a merge, never after.** Run `git fetch origin main &&
  git merge-tree --write-tree origin/main HEAD`. If it reports a conflict, merge main in and fix
  it first (never rebase or force-push, 7.48). Do not turn on auto-merge or ask for a merge on a
  PR you know conflicts: it cannot land, and it wastes a full test run.
- **Before you open a PR, check the open set** for one that already touches the same files or row
  (list the open PRs and read their titles and files). Add to it or wait for it rather than
  opening a rival.
- **Say what you abandon.** A PR you are not finishing: mark it draft (it stops taking runners)
  and tell the director it can be closed. Never close it yourself (Director Bible 7.50).

## Review boards and imagery (director, 2026-11-26)

Review boards, WIP films, reference photos and aerial or satellite imagery go to the private repo
`aussierulesdynasties/afl-review-archive` (same `.claude/review/` paths), never to this public repo, and never
as a "save work in progress to main" commit. `.claude/review/` is ignored here.

## UI and writing

Before touching any screen, copy or vignette, load the `afl-ui-writing` skill (visual identity, readability, colour, consistency, review test).

## Assigned flavour and styling work (director, 2026-10-06)

- **Flavour FL-001-FL-008:** scope and rulings in [the Director Bible](docs/DIRECTOR_BIBLE.md). Every addition has zero gameplay effects and must look distinct from real game information; new ritual/farewell vignette scenes are authorised (shared 2.5D art, tactical-scene gates kept).
- **Styling STYLE-01-STYLE-08:** scope and rulings in [the Director Bible](docs/DIRECTOR_BIBLE.md). Dark Android first. Light theme removed (director 2026-11-26: "please remove 'light mode' from the game"): dark is the only appearance. A visual treatment merges only after the director approves its look; green CI is not enough.
- The Training player-row name/secondary-line stack is a confirmed vertical-alignment defect.

## Skills

Learnings and spin-off skills follow the global rules in `~/.claude/CLAUDE.md` (add a learning only with evidence). A project skill is named `afl-<topic>` and says which general skill it extends.
