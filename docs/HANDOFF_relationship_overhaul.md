# Handoff: Player Relationship Overhaul (Crusader Kings inspired)

Written 2026-11-27 ~06:40 UTC for a fresh Claude on a different account. The project threads this
work was done in are NOT readable from that account, so everything needed is in this file and in the
files it points to. Companion files in `docs/handoff/`:

- `relationship_overhaul_blueprint.md` - the full audit and blueprint doc (data model, hooks, phases, the 9 locked decisions).
- `relationship_overhaul_card_audit.md` - the full 773-card event deck audit (per-card list: `relationship_overhaul_event_card_audit.csv`).
- `transcripts/` - every project thread and the project chat, exported as markdown (raw record).

The director ("Baggins", GitHub `gabebartolo-spec`) designs; Claude builds. Project instruction:
**"Crusader Kings is the main inspiration."**

---

## 1. Working rules from Baggins (follow these exactly)

1. **Old-save compatibility is NOT required** (2026-11-26). Do no migration or back-compat work.
2. **Split work into narrow threads/sessions**, each with one limited scope. Do not overburden one session.
3. **Technical guardrails only.** The legacy Director Bible rulings that restricted this overhaul are retired
   (see section 3). What stays: plain-dictionary state on `GameState`; 18-club parity (every rule runs at
   every club, the AI coaches answer by the same rules); no mindless weekly click-chores (about one card a
   week, two in big/crisis weeks); `MatchSim` stays isolated, reached only through morale/form and
   Togetherness, verified with a paired `tools/balance.sh match 1000` run.
4. **Baggins never reviews code.** Do not ask them to review PRs. Sessions merge their own PRs once CI and
   the paired balance check pass. Show Baggins outcomes instead: screenshots (attach the PNGs directly,
   check them yourself first for faults) and plain-English summaries.
5. **Never idle waiting on merges or CI.** Stack branches on unmerged work and keep building; merge main in
   as things land. ("surely you can do something else while you wait")
6. **Real-named players can appear on any card**, including personal and off-field discipline cards
   (the 2026-11-09 rule stands; test `_test_private_cards`). Only *invented scandals* are banned. Decided
   2026-11-26 by decision card; do not raise it again. Leaks and board whispers naming real coaches are fine.
7. **Never use the user's C: drive for scratch/temp files**; clean up after yourself.
8. **Never react with emoji** (especially eyes) to Baggins' messages; reply in words.
9. **Questions: one at a time, as a decision card (or single clear question) with your recommendation first.**
   Never several questions or option lists in prose - Baggins will not answer those
   ("i only answer questions that follow the rules"). Before asking, search `docs/DIRECTOR_BIBLE.md`,
   `docs/TODO.md` and `CLAUDE.md`; never ask something a ruling already answers.
10. Be fast. Baggins dislikes slow, over-thorough document work ("its just a document not the bible").
11. Every club gets every buff/cost; options are equal (CLAUDE.md). Numbers are first guesses; balance is the
    director's call after their own playtest - never declare balance settled.
12. **Fix CI the moment it fails, without being asked** (2026-11-27: "fix it the very second it fails. ill be
    furious if i have to ask again"). After every push, subscribe to the PR's activity and also schedule a
    check-in about every 15 minutes, because events can be missed. Watch the checks until the PR merges.
13. **Before you push, check main and the other open PRs for overlapping changes** (2026-11-27). Seeded-season
    checksums (`tests/fixtures/awards_round4_snapshot.txt`, `GOLDEN_SEASON` in `tests/test_dataset.gd`) clash
    with any PR that changes the season: merge main in the moment anything lands, re-record, then push.

Also read the repo's `CLAUDE.md` (PR cap of 3 ready PRs, push once not in drips, check for conflicts
with `git merge-tree` before asking to merge, never rebase/force-push shared branches, never close a PR yourself).

---

## 2. The vision (Baggins' brief, 2026-11-26, condensed)

Replace the shallow weekly event-card +/- relationship system with a deep, roleplay-driven interpersonal
and club-politics system:

1. **You are the dynasty leader (senior coach)**, balancing locker-room **Respect** against hardline
   **Authority**, personal relationships, and kept/broken promises.
2. **Staff are the Council**: assistant/line coaches, List Manager, Head of High Performance. They have
   personalities, competence, loyalty and agendas; hiring, firing or overruling them has political fallout.
3. **Players are vassals**: opinion built from stacked, time-decaying modifiers ("Dropped for finals: -30");
   temperaments; ambitions; emergent **factions/cliques** that escalate to ultimatums; **promises as hooks**.
4. **Stateful narrative event engine**: cards triggered by temperament, ambition and faction, with Council
   members pitching competing advice and choices leaving lasting opinion trails.

### The 9 locked decisions (Baggins, 2026-11-26 08:33Z)
1. Sparse player-to-player bond graph (close mates, rivals, mentor/protege, leadership allies, family).
   Dropping/trading/backing a player affects his mates and rivals.
2. Opinion modifiers decay weekly toward 0; kept/broken promises, finals snubs, betrayals are permanent or long-tail scars.
3. Temperaments for ALL players (real and generated), grounded in on-field/locker-room record only.
4. 8 temperaments: clubman, mercenary, competitor, mercurial, professional, fiery, leader, quiet_achiever; 1-2 each.
5. Council members pitch advice in their own signed voice (single-narrator rule retired).
6. 8-seat Council: the 6 coaching roles + List Manager + Head of High Performance, at all 18 clubs.
7. Live Respect and Authority for the senior coach, moved by decisions; coach archetype sets only the starting lean.
8. Full transparency on drill-down: exact marks, bond links, weeks left, Respect/Authority effects on profile and selection preview.
9. A dedicated **Club Politics / Inner Circle** screen (Council loyalties, cliques/bonds, factions, coach standing), not busywork.

Director Bible records these as rules **5.167-5.177**; retired rulings listed as **S26-S32** and **3.S5a**
(old #8/1.8, #38 RPG-009 caveat, #106, #107, #156, Copy Voice 3.38, 2026-10-11 and 2026-11-08 restrictions).
`grep -n "5\.1[67][0-9]\|S2[6-9]\|S3[0-2]" docs/DIRECTOR_BIBLE.md` finds them.

---

## 3. Phase plan and what each piece built

Phase numbering (renumbered by the coordinator 2026-11-26): **Phase 1** core systems; **Card Pass 1**;
**Phase 2 Council**; **Phase 3 Factions**; **Ambitions & Council-Faction Wiring** follow-up;
**Phase 4 full narrative card overhaul** (next); **Phase 5 Club Politics screen** (after).

All code follows the repo pattern: authored JSON in `data/relations/`, validated by the class that reads it;
static `RefCounted` rule classes in `scripts/sim/`; runtime state as plain dicts on `GameState`.

### Phase 1a - Opinion engine (`scripts/sim/Opinion.gd`, `data/relations/modifiers.json`) - MERGED (#2234)
- `Trust.gd` is now `class_name Trust extends Opinion`, so every old `Trust.*` call still works.
- Opinion = permanent base (trust units -100..100) + live fading **marks**. Shown opinion 0..100 = `50 + t/2`.
- Key API: `Opinion.value(rel,key)` (trust incl. live marks), `Opinion.opinion(t)` (to 0..100), `base()`,
  `change(rel,key,d,why,year,when)` (permanent, the old Trust.change), `add(rel,key,mark_key,year,when,club,scale,src,fade_scale)`,
  `add_raw`, `fade_round(rel)`, `drop_other_clubs(rel, club_of)` (marks are about the current coach, cleared on a club move),
  `weeks_left(m)`, `breakdown(rel,key)` -> rows `{why, points, weeks(-1 = stays), tag, k, src}` biggest first,
  `mark_text(b)` ("Left out while fit: -4. Gone in 4 weeks."), `drop_mark(ovr, is_final)` ("dropped" / "dropped_star" at OVR 78+ / "dropped_final"),
  `preview(rel,key,mark_key,scale,src)` (change without applying), `card_move(rel,key,d,why,year,when,scar,club)`.
- `src` keeps one mark per source (two mates dropped = two marks; same mate dropped again renews, not stacks).
- Card `trust` ops now go through `Opinion.card_move`: by default d trust becomes a live mark of d/2 points fading
  0.5 a round, keyed by reason; with `"scar": true` it moves the permanent part (old behaviour).
- Marks (v = opinion points, fade = points lost per round, 0 = stays): dropped -4/1; dropped_star -8/1;
  dropped_final -20/0.5 (scar); picked_final +4/0.25; promise_kept +10/0.25 (scar); promise_broken -15/0 (scar);
  saw_promise_broken -3/0.5; mate_dropped -2/1; mate_traded -6/0.5; mate_backed +2/1; rival_picked -3/1;
  rival_traded +3/1; betrayal -25/0 (scar). Council phase adds coach_sacked -5, coach_left -2, advice_taken +4,
  advice_overruled -4, agenda_served +2, agenda_crossed -2 (and more on the council branch).
- Marks land after each round in `GameState._opinion_after_round` (left-out and finals marks at every club).
- **Morale drift**: `ClubLife.morale` drifts 1 point a round toward the player's opinion of his coach, at all 18 clubs.
  Season probe: league average morale 86.4 -> 82.2, morale form lift +1.66% -> +1.22%. **Baggins approved as-is**
  ("82 gives healthier headroom"). Paired 1,000-match balance: single matches unchanged.
- The word "modifier" is on the banned copy list (`CopyRules`); UI must not say it.
- Test: `tests/opinion_body.gd` / `tests/run_opinion_tests.gd` (a -5 card mark at fade 0.5 is gone at round 10).

### Phase 1b - Temperaments (`scripts/sim/Temperament.gd`, `data/relations/temperaments.json`) - MERGED (#2156)
- Every player holds 1-2 of the 8 (second_chance 0.5), stored as `p["temperament"]`, deterministic from the id and
  his football record (named captain -> leader; long one-club career -> clubman; moved clubs -> mercenary; poor discipline -> fiery).
- `Temperament.scale(p, lever)` -> float multiplier (product over his temperaments, clamped 0.5..2.0).
  Levers: dropped, backed, promise_kept, promise_broken, discipline, praised, bond, decay (>1 forgets faster),
  respect, authority, faction (added by factions). Also `of(p)`, `has(p,key)`, `label`, `describe`, `reactions(p)`.
- Integration tightened leaders: `start_weight {"leader": 0.05}`, `leader_from 62` -> 81 leaders league-wide (was 185; 1-8 a club, following each club's real leadership group).

### Phase 1c - Bonds (`scripts/sim/Bonds.gd`, `data/relations/bonds.json`) - MERGED (#2158)
- `gs.bonds = {"v":1, "year":int, "by": {pid: {other_pid: {"k": kind, "s": 1-3, "y": since_year, "rel": family word}}}}`;
  `by[A][B].k` is what B is TO A. Kinds: mate, rival, mentor, protege, ally, family (rel words: brother, twin brother,
  cousin, father, son, grandfather, grandson, uncle, nephew - real family from `FamilyTies`).
- Up to 4 active ties plus family. Mates: similar age, same draft year or state. Rivals: same position, similar rating.
  Mentor/protege: kid 21 or under with a senior at his position. Allies: captain and vices. Each season ties to departed
  players drop, cross-club ties fade, a protege of 25 becomes a mate.
- `Bonds.of(gs.bonds,pid)`, `Bonds.ACTOR_ROLES`; `GameState.bond_actor(pid, role)` (close_mate, positional_rival, mentor,
  protege, brother, family, ally, incumbent); `GameState.bond_ties`; `GameState.bond_fallout(pid, action)` with
  action drop/trade/delist/back -> rows `{id, kind, opinion, mark, scale, why}`; `_bonds_refresh()` after `_captaincy_refresh()`.
- Family-bonds lint exemption added (the old "family is bio only" rule is retired; settled).

### Phase 1d - Promises + Respect/Authority (`scripts/sim/Promises.gd`) - MERGED (#2233)
- One door for every promise: kinds run, game, dev_games, win (consolidates Backing, expects_game, dev-talk promises, `gs.coach_word`).
- `gs.coach_standing` (per club): Respect and Authority 0..100, START 50. Archetype lean (each sums to zero):
  Father Figure +10/-10, Hardline -10/+10, Analytical -5/+5, Gambler +5/-5.
- KEPT: run +4R, game +2R, dev_games +4R, win +2A. BROKEN: run -6R, game -4R, dev_games -6R, win -2A
  (the +1 Authority on a broken promise was REMOVED by the integration PR, Baggins' call: breaking your word only
  hurts Respect and coach_word). Dropping fit players builds Authority (up to +2 a round, DROP_ROUND_MAX 2).
- Subject of a broken promise keeps the permanent Trust.change; up to 6 line-mate witnesses get `saw_promise_broken`;
  a kept promise adds `promise_kept`. `Promises.preview_drop(gs, pid)` feeds the selection preview.
- API: `standing`, `respect`, `authority`, `move`, `standing_reasons`, `season_end`, `rebase`, `made`, `settle`, `witnesses`, `after_match`.
- Rival coaches play by the same rules. Standing does not reach matches.

### Phase 1e - UI (`scripts/ui/PlayerSheet.gd`, `scripts/ui/SelectionScene.gd`, `scripts/ui/RelationsView.gd`) - MERGED (#2226)
- Player profile relationships block: temperament, opinion of you, and a **Why** button opening the full breakdown
  (what's fading and weeks left, scars that never fade, what he remembers, how he takes your calls, mates and rivals each a tap away).
- Team selection: a fit player's profile shows **"If we leave him out this week"**: his opinion change, any promise broken,
  which mates/rivals react, Respect and Authority before and after. Preview only. **Baggins approved the screenshots.**
- Captures: project files `relations-ui/*.png` and `relations-wiring/*.png`.

### Phase 1f - Card engine (`StoryEngine.gd`, `StoryDeck.gd`, `ClubStories.gd`) - OPEN PR #2231 (ready), branch `claude/project-thread-ja7zjv`
(Re-opened copy of the closed #2164.) Baggins' four engine upgrades:
1. **3-tier priority queue**: Tier 1 urgent (due arc beats, faction ultimatums, broken-promise reckonings, Council leaks);
   Tier 2 reactive (fresh bond fallout, temperament/ambition clashes, Council splits; expire within ~4 weeks);
   Tier 3 ambient. Still ~1 card a week, a second only when the first is urgent.
2. **Slot binding**: cards declare `actor_b` (close_mate, positional_rival, mentor, protege, brother, incumbent) and
   `advisors` (list_manager, high_performance, line_coach, senior_assistant, development), tokens `{player_b}`,
   `{advisor_name}`, `{advisor_role}`; cards skip when nobody fits. `ClubStories.bond_links(gs,pid)` -> {role:[ids]}; who `"b"` in `_targets`.
3. **`club_variants`** text overlay so consolidated families keep each club's local words.
4. **`scar` flag** on card trust ops. Tagged 8 of the 10 planned scar cards (baby due, dad in hospital, finals fitness test,
   racing the clock in a GF, finals experience pick, in the papers, backed kid struggling, veteran form/drop).
   `captain_succession_next` and `star_wants_out` had no card trust cost; Card Pass 1 adds them.
   Two new backlog dilemmas: **Cross-Club Grudge Match** and **Locker-Room Lobbying** (in the card audit doc).

### Phase 1 Integration (wiring) - OPEN draft PR #2229, branch `claude/project-thread-ep2z5b`
(Re-opened copy of the closed #2180.) Contains Opinion+Temperament+Bonds+Promises+card engine+UI merged, plus:
temperament-scaled marks (`scale = Temperament.scale(p, lever)`, `fade_scale = Temperament.scale(p,"decay")`),
bond fallout on drop/back/trade/delist at the acting club only, live Respect/Authority in the preview, no Authority for a
broken promise, leaders ~4-5 a club. Real-tap test proves the preview's numbers are what the round applies
(`tests/test_relations_wiring.gd`). Paired 1,000 matches: identical; season morale 82.5-82.7 either way.
Example in captures: leaving out Nick Daicos while promised a game shows his hit, the promise cost, Josh Daicos and
Darcy Moore -5 each, Respect 51 -> 47, +1 Authority (from the drop itself).
Temperament levers "respect"/"authority" are still unread (meant for the Council era).

### Card Pass 1 (Phase 1 hooks only) - BUILT, NOT YET A PR
- Scope set by Baggins: delete the 5 retired cards; wire weekly and club promise cards (incl. the 14 untracked
  promises) to Promises.gd; trust/scar costs on `captain_succession` and `star_wants_out`; wire bond-seeding and
  temperament cards; merge the 14 homesick club cards into one card with `club_variants`. NOT the full 179-card rewrite
  (Council-voice rewrites wait for Phase 2; faction/discipline rewrites for Phase 3).
- Done: 5 retired, 11 of 14 untracked promises tracked (3 left out because they promise nothing checkable: "a review",
  "a plan, not a result", "open it up"), star scar, 7 bond cards, temperament cards, one homesick card. Card tests pass;
  paired 1,000 matches: no change.
- Where it is: commit `85e7a8429` "Card Pass 1: Phase 1 hooks on the event cards" in the history of branch
  `claude/project-thread-ja7zjv` (it was taken back out by revert `bdfa58d81`). Also saved as
  `/mnt/project-files/card-pass-1/0001-Card-Pass-1-Phase-1-hooks-on-the-event-cards.patch` and `card-pass-1.bundle`.
  To land: after #2231 and #2229 merge, branch from main, `git cherry-pick 85e7a8429` (resolve against main), test, PR.
  Touches StoryEngine, StoryDeck, ClubStories, Promises (card promise kinds in coach_word.open) and test_story.

### Phase 2 - The Council (`scripts/sim/Council.gd`, `data/relations/agendas.json`) - OPEN draft PR #2204, branch `claude/project-thread-tagzda` (base: ep2z5b)
- 8 seats at all 18 clubs: senior_coach, senior_assistant, line_coach (MID), fwd_coach, def_coach, development, plus office
  jobs **LM** (List manager) and **HP** (Head of high performance) - generated people stored in `gs.council.office`, not CoachMarket jobs.
  Existing `StoryEngine.ADVISOR_SEATS` keys unchanged; fwd_coach/def_coach added.
- Agendas (one per person, weighted by job): youth "Bring the kids through", win_now, standards, look after the players,
  mind the bodies, build the list. Each agenda has `weigh` (how a card choice's ops suit it) and `voice` lines by manner
  (blunt, measured, warm), signed in the person's own name on the card.
- Loyalty = his opinion of the senior coach, stored at `gs.relations["s:<id>"]` in the Opinion shape (fades like player opinion).
  LOYAL_LINE 65, RESTLESS_LINE 35, WALK_LINE 25.
- One signed pitch per card: card option may carry `"pitched_by": "<seat key>"`. Taking advice +4 loyalty; going against -4
  loyalty and +1 Authority.
- Season end: anyone at loyalty <= 25 walks out, at every club. When a coach leaves/is sacked his players get coach_left/coach_sacked.
- `Council.faction_sway(gs, club, f) -> int`: each council member attached to a faction member gives -1 if loyal (65+),
  +1 if restless (<=35), capped +-2.
- Staff screen (`scripts/ui/StaffScene.gd`) **redesigned** after Baggins called the first PC version "hideous": your card
  shows Respect and Authority as big figures in club colour; each staff card has job over name, loyalty as a big number
  with its word, agenda, why the number moved (quieter text), four grades on the right; club-colour stripe on top; PC
  4 across x 2 rows, fits 960x540 without scrolling; phone one column. Captures: project files `council/staff_redesign_*.png`.
  Baggins has not yet given a verdict on the redesign.
- Tests: `tests/run_council_tests.gd` (12 tests, 563 checks incl. a real tap). Paired 1,000 matches: all B-A 0.00.
  3 known local failures in Create-a-player 3D preview need MetaHuman files (cloud can't fetch); not this PR.

### Phase 3 - Factions (`scripts/sim/Factions.gd`, `data/relations/factions.json`) - OPEN draft PR #2203, branch `claude/project-thread-k6d7jr` (base: ep2z5b)
- State `gs.factions[club]` = array of `{k, members, leader, tag, pressure, since, state, demand}`; states forming/demanding/ultimatum.
- Kinds: **fringe** (left out / soured ambition: "a fair go at selection"), **broken_word** (saw you break your word),
  **senior** (senior players who stopped rating you).
- A player joins when opinion of coach < join_line 47 and his grievance fits, scaled by temperament lever `faction`
  (fiery/mercurial join fast, professionals/quiet achievers slow); need join_need 4. min 3 members, max 8; leave_line 55.
  Pressure +per_member 2 per member per round + council sway; ease 3 on quiet rounds; demand_at 30; ultimatum_at 75;
  after 4 unanswered rounds it breaks and the leader asks to be traded at season end.
- Card about the group's leader with options **meet** (fringe: pick the leader next week), **refuse** (pressure jumps +25),
  **split** (break it up: leader asks to be traded). Op `{"op":"faction","do":"meet"|"refuse"|"split"}`. Cards `faction_*`
  in `data/stories/leadership.json`, advisors development/senior_assistant/line_coach (required false).
  Each option shows exact costs (opinion, Togetherness, Respect, Authority). standing table: met [+2R,-3A], met_late [+1,-5],
  refused [0,+2], split [-2,+3], broken [-3,0].
- Reaches the match only via morale (demanding -3, ultimatum -6) and Togetherness. Rival clubs run the same rules; their
  coach answers by his own standing; league news reports when a rival's group is broken up.
- Tuned: ~12 groups a league season, 8 demands (~1 demand card for you every 2 seasons) - superseded by the wiring PR's tuning.
- `Factions.council_sway` returns 0 on this branch; whichever of #2203/#2204 merges second sets its body to
  `return Council.faction_sway(gs, club, f)` (the ambitions branch already does).
- Tests: `tests/test_factions.gd` (13 tests). Paired balance: no change. Captures: project files `factions/*.png`.

### Ambitions & Council-Faction Wiring - OPEN draft PR #2223, branch `claude/project-thread-9czkkr` (contains #2204 and #2203)
(Re-opened copy of the closed #2209.) Baggins' four gaps:
1. **Ambitions** (`scripts/sim/Ambitions.gd`, `data/relations/ambitions.json`), stored at `p["ambition"]`. At season start
   each eligible player may hold one (hold_chance 0.55), picked by kind weight x temperament lean. Kinds: senior_spot
   (age<=22, career<=20, goal 6 games), bigger_role (22-30, 20+ games, out of side, 15 games), milestone_push (career 30+,
   reach next milestone 50/100/.../400), win_now (28+, 100+ games, club wins 12), leadership_role (named captain/vice),
   big_contract (club re-signs him). States active/met/soured/lapsed. Met: `ambition_met` opinion lift + 1 Respect.
   Soured: lasting grievance mark `ambition_soured` (tag ambition) read by the fringe faction, plus ask_out 0.4 chance (x faction lever)
   of a season-end trade request (`TradeRequests.gd`). Injury -> lapses without blame. Shown on PlayerSheet.
2. **Two-way advisor clashes**: a card's `clash` seats two Council members on competing options. Siding with A: A +4, B -3;
   a third option of your own: both -2, you +2 Authority (OWN_WAY).
3. **Disloyal coaches with teeth in season**: a line or development coach (TEETH_JOBS MID/FWD/DEF/DEV) at loyalty <= 35
   loses his man-management softening when you drop his line's players, and becomes advisor seat `restless` on three new
   cards: leaking the side to the papers, getting in the board's ear, backing a players' group.
4. **Council -> faction pressure + escalation tuning**: a restless coach tied to a group by line or agenda pushes it faster
   (STIR 2, STIR_MAX 4). `factions.json` gained `climate` (low_respect 45, high_respect 60, losing_run 3, snubbed 10, join_ease,
   quiet_join, rough_step, quiet_ease) and `club_wait 6`. Result in a test season: rough clubs 1.3 flashpoints each (1-3),
   four settled high-Respect clubs almost none (previously ~8 league-wide a season).
- Tests: `tests/test_ambitions.gd`; touched suites green except story-suite failures that also fail on the base branch.
  Paired 1,000 matches: no change. Captures: project files `ambitions/*.png`.

### Phase 4 - Full narrative card overhaul (NOT STARTED, next)
- Rewrite the 179 "rework" cards (55 weekly, 103 club, 7 of 14 coach arcs) and add ~40 new dilemmas (bonds, temperament,
  ambition, promises, Respect/Authority, Council, factions, + Cross-Club Grudge Match and Locker-Room Lobbying).
  Staged passes from Baggins' plan: Pass 2 bonds/temperament + 16 new dilemmas (14 homesick merge done in Pass 1);
  Pass 3 Council voices + 8 seats; Pass 4 factions + Respect/Authority + merge the 20 nights-out discipline cards;
  Pass 5 scar callbacks. 16 pick-the-kid club cards also to consolidate. 8 of the 45 year events should shift Respect/Authority.
  Rival clubs never draw cards, so their parity must come from AI-side rules.
- Full per-card verdicts: `docs/handoff/relationship_overhaul_card_audit.md` and the CSV.

### Phase 5 - Club Politics / Inner Circle screen (NOT STARTED)
One first-class view: Council loyalties, key cliques/bonds, active factions, coach Respect/Authority. Must not become
weekly busywork. Load the `afl-ui-writing` skill first; mobile portrait first; Baggins approves the look from screenshots.

---

## 4. Merge session status (updated 2026-11-27 ~07:30 UTC, supersedes the table below)

**Merged:** #2231 card engine (06:29Z). Everything else (Card Pass 1, integration, Council, Factions, Ambitions)
is on ONE combined branch, `claude/project-thread-ucazbs`, opened as one PR to main (see the PR list; title starts
"Relationship overhaul: Card Pass 1, integration, Council, Factions and Ambitions"). Card Pass 1 has no other PR:
it was applied from the saved patch, not the old commit.

### What is in the combined PR (branch `claude/project-thread-ucazbs`)

One branch on top of main holds everything else, because the stacked draft branches were made
before main's history was rewritten for the repo-size clean-up and no longer merge cleanly:

1. **Card Pass 1** (`9f886c54`, applied from the saved patch `card-pass-1/0001-...patch`): retires five
   cards, card promises (senior game, new deal, a future here, finals, wins) settled by
   `Promises.check_open` / `Promises.card_season_end`, bond cards with `actor_b`, the 14 club homesick
   cards folded into one `family_homesick` with `club_variants`.
2. **Phase 1 integration** (from draft PR #2229, branch `claude/project-thread-ep2z5b`): temperaments size
   opinion marks, bond fallout on drop/back/trade/delist at the acting club, live Respect/Authority in the
   drop preview, a broken promise builds no Authority (director 2026-11-26), about 4-5 leaders a club.
3. **The Council** (from draft PR #2204, branch `claude/project-thread-tagzda`): `scripts/sim/Council.gd`, eight
   seats at all 18 clubs, agendas (`data/relations/agendas.json`), loyalty at relations `s:<id>`, signed
   pitches, walk-outs at loyalty 25 or less at season end. Includes the Staff screen redesign.
4. **Factions** (from draft PR #2203, branch `claude/project-thread-k6d7jr`): `scripts/sim/Factions.gd`,
   `data/relations/factions.json`, kinds fringe / broken_word / senior, `faction_*` cards in leadership.json.
5. **Ambitions and Council-faction wiring** (from draft PR #2223, branch `claude/project-thread-9czkkr`):
   `scripts/sim/Ambitions.gd` on `p["ambition"]`, two-advisor clashes on `card["clash"]`, restless coaches,
   `Factions.council_sway` calls `Council.faction_sway`.

How it was built: main, then the patch, then `git cherry-pick` of only each branch's own commits
(3ab72aa8, 47839653; 436d6a70, 3887bf44, 262cbbb3; 59ad34f4, ebd1c8a9; 093a4d5c). Conflicts resolved:
`Promises.gd` KEPT/BROKEN tables (Card Pass kinds kept, run/game/dev_games break for 0 Authority),
`GameState.gd` (bonds, council and factions state all kept; `_opinion_after_round` passes
`Factions.morale_shift` and then calls `Council.after_round`), `modifiers.json` (every mark kept once).
The resulting Council/Factions/Ambitions code is identical to branch 9czkkr.

Once the combined PR merges, draft PRs #2229, #2204, #2203 and #2223 are superseded and can be closed
(agents do not close PRs: tell the owner).

### Tests fixed on the combined branch

The draft branches skipped the game tests in CI, so these had never run with the overhaul in. Failing on
9czkkr alone too, so not caused by the combining:

- `tests/test_story.gd`: faction cards read a group's facts (`{faction_size}`), so the generic card-wording
  tests skip them (`_faction_card`; tests/test_factions.gd covers them). Hints skip a card whose second
  player nobody fits. The size test accepts bond lines and "opinion of you falls N". The expects-game size
  is scaled by the player's temperament (`facts.broken_scale`), as `StoryEngine._broken_words` does.
- `tests/test_club.gd`: a man out this week may drift one step (his opinion, a faction), which is not a
  sting; the no-room promise check reads the permanent part (`Trust.base`), not fading marks.
- `scripts/sim/Promises.gd` `_card_of`: reads the open card promises without creating the list, so
  `preview_drop` stays read-only (tests/test_promises.gd).

Still to confirm on CI: the full `story` suite (over 20 minutes locally on 4 cores, it timed out there) and
`_test_trust_in_play` (it fails when run alone even on main, so it needs the full suite to judge).

### Match engine

No MatchSim or match file changes in the diff (`git diff --stat origin/main -- scripts/sim/MatchSim*.gd`
is empty). Run `tools/balance.sh match 1000 --a-root <main checkout> --b ""` and paste the table in the PR
before merging, per CLAUDE.md.

### Next steps (merge session)

1. Get the combined PR green (read failed shard logs; fix; push once). Merge it (squash).
2. Tell the owner #2229, #2204, #2203, #2223 can be closed.
3. Not built yet: temperament levers "respect"/"authority" are still unread (Phase 2 follow-up). Captain
   succession and `star_wants_out` scars need a trust op or a scar in Captaincy.gd.
4. Visuals awaiting the owner's look are in the project files (council/, factions/, ambitions/,
   relations-ui/, relations-wiring/ captures).

## 4b. Live PR / merge state as it was at ~06:35 UTC (before the merge session)

History: on 2026-11-26 15:04Z Baggins (or their CI session) drafted every open PR; at ~22:06Z main's history was
rewritten (CI/asset cleanup moving review imagery and ground models to private repos) and the open overhaul PRs
(#2161, #2162, #2160, #2164, #2180, #2209) were closed unmerged. Branches survived, rebuilt on the new history, and
were re-opened as new PRs. A separate session ("Merge all open overhaul work", started 06:22Z 27 Nov) is merging
everything now. **Re-check live state first** (`gh api repos/aussierulesdynasties/Afl-auto-battler/pulls?state=open`;
GraphQL is blocked in cloud sessions, use REST).

| Piece | PR | Branch | State |
|---|---|---|---|
| Temperaments | #2156 | claude/project-thread-37gdwz | merged 2026-11-26 13:32Z |
| Bonds | #2158 | claude/project-thread-3gfasf | merged 2026-11-26 13:57Z |
| Phase 1 UI | #2226 (was #2160) | claude/project-thread-z9a1sb | merged 2026-11-27 00:05Z |
| Promises + Respect/Authority | #2233 (was #2162) | claude/project-thread-p3ltql | merged 2026-11-27 00:26Z |
| Opinion engine | #2234 (was #2161) | claude/project-thread-tclzy6 | merged 2026-11-27 05:06Z |
| Card engine | #2231 (was #2164) | claude/project-thread-ja7zjv | open, ready |
| Phase 1 integration | #2229 (was #2180) | claude/project-thread-ep2z5b | open, draft -> main |
| Card Pass 1 | none yet | commit 85e7a8429 | built; cherry-pick after #2231/#2229 |
| Council (Phase 2) + Staff redesign | #2204 | claude/project-thread-tagzda | open draft, base ep2z5b (retarget to main after #2229) |
| Factions (Phase 3) | #2203 | claude/project-thread-k6d7jr | open draft, base ep2z5b (retarget to main after #2229) |
| Ambitions & wiring | #2223 (was #2209) | claude/project-thread-9czkkr | open draft -> main; contains #2204 + #2203 |
| PR cap fix | #2238 | claude/project-thread-vmkoek | open draft (not overhaul) |

**Merge order:** #2231 card engine -> #2229 integration -> Card Pass 1 PR -> #2204 Council -> #2203 Factions (set
`Factions.council_sway` to call Council) -> #2223 Ambitions. Since #2223 already contains Council and Factions, an
alternative is to merge #2223 alone after #2229 and close #2204/#2203 as superseded (tell Baggins; never close PRs yourself).
Each: merge main in (never rebase), `git merge-tree --write-tree origin/main HEAD` for conflicts, run touched suites
(`tools/run_tests.sh opinion`, `relations_wiring`, `relations_ui`, `promises`, `council`, `factions`, `ambitions`, `story`, `club`),
paired `tools/balance.sh match 1000 --a-root <main checkout> --b ""`, paste the table in the PR, mark ready, merge on green.

---

## 5. Known issues

- **PR cap check fails on every PR**: its workflow token (`MERGE_TOKEN`) has only `repo` scope; `gh pr edit/view/ready/comment`
  need `read:org` ("The 'login' field requires one of the following scopes: ['read:org']"). #2238 (draft) rewrites it to REST +
  bare GraphQL mutations; #2236 (merged 26 Nov) removed the PR cap bot entirely, so the cap is now enforced by hand
  (max 3 ready PRs, CLAUDE.md). A red PR-cap check on a PR is not caused by that PR.
- **Story suite** (`test_story`) is slow (10+ min; times out on a 4-core container) and had failures on the stacked branches that
  also fail on the base branch; CI runs it properly.
- Create-a-player 3D preview tests fail locally without MetaHuman files (`tools/epic_assets.sh fetch`, private repo).
- CI is a shared pool of ~20 runners; push once, not in drips; subscribe to PR activity after a push.
- Temperament levers `respect`/`authority` are defined but not yet read anywhere.
- 3 of the 14 untracked card promises remain untracked (nothing checkable); Baggins may want different wording.
- All numbers (mark sizes, faction thresholds, ambition odds) are first guesses for Baggins to tune after playtesting.

---

## 6. Next steps for the new account

1. Check what the merge session landed (`git log origin/main --oneline -30`, open PR list). If the combined PR from
   `claude/project-thread-ucazbs` is not merged, finish it (section 4, "Next steps (merge session)").
2. Card Pass 1 is in that combined PR (no separate PR needed).
3. Get Baggins' verdict on the Staff screen redesign (one decision card, screenshots attached, recommendation first),
   unless it has already been given.
4. Phase 4 (card overhaul) in narrow parallel sessions per pass (section 3), then Phase 5 Club Politics screen.
5. Record progress in `docs/TODO.md` (it owns status and order) and any new rulings in `docs/DIRECTOR_BIBLE.md` (with consent).

## 7. Artifacts and captures

Baggins' project shared folder (`/mnt/project-files/`, may not be reachable from the other account) holds:
`ambitions/` (ambition_profile, ambition_clash, ambition_restless .png), `council/` (council_card_phone, council_staff_*,
staff_redesign_pc_1280x720 / 960x540 / adelaide, staff_redesign_phone .png), `factions/` (faction_card, faction_result,
faction_profile .png), `relations-ui/` and `relations-wiring/` (profile breakdown, drop preview), `card-pass-1/` (patch + bundle),
`event-card-audit/event_card_audit.csv`, `handoff/` (this handoff and transcripts). The capture scripts are in the branches:
`tools/visual/capture_faction.gd`, `tools/visual/capture_ambition.gd`, so any capture can be retaken.
Claude Docs (account-bound, likely unreadable from the new account; copies are in `docs/handoff/`): blueprint
https://claude.ai/artifact/9Rs7Xq8ERN9fzZ3W2AgVFz, card audit https://claude.ai/artifact/Ds3ZHGS6LrG4wNx2gtiGpn,
Phase 1 report https://claude.ai/artifact/GCLWwpayxL7CmVc36Wok1k.
