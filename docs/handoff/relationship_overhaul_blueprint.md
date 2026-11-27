
# Player Relationship Overhaul: Audit & Blueprint

2026-11-26 · @Baggins


## Summary

The game already has most of the scaffolding this overhaul needs, so the plan grows the existing Trust and story systems rather than replacing them. A player's opinion of you (0 to 100, every move with its reason), three culture strands, four kinds of promise, a 150-card story deck with arcs and flags, six staff jobs per club and the Hardline Disciplinarian and Father Figure coach archetypes are all built and saved today.

What is missing is what makes Crusader Kings feel alive: modifiers that fade over time, personalities that change how a player takes the same event, ambitions he pursues, staff with their own agendas, and groups of unhappy players who act together.

**Update 2026-11-26:** the director retired the six conflicting rulings and locked all nine decisions (below). The Director Bible now records them as rules 5.167 to 5.177, with the retired rulings listed under 5.S26 to 5.S32 and 3.S5a. Phase 1 is being built in five parallel threads: Opinion engine, temperaments, bonds, promises with Respect and Authority, and the Phase 1 UI. A sixth thread is auditing the event card deck.

Recommended order: Opinion engine and promises, then ambitions, then the Council, then factions, with the matching UI and story cards shipped inside each phase rather than saved for the end.


## Codebase audit

Audited at main `d1974a9` (2026-11-26). Rules live in static `RefCounted` classes; all state lives in plain dictionaries on `GameState` and is saved as-is, so an older save loads with missing keys as neutral.


### What exists

| Area | Files | What it does today |
|---|---|---|
| Opinion of you | `scripts/sim/Trust.gd` (134 lines) | One map, `GameState.relations`, keyed `p:<id>` (keys `c:`, `j:`, `b:` reserved for coaches, journalists, board). Trust -100..100, shown as opinion 0..100. Each move capped at 20, keeps its reason (last 8). Never drifts back. Bands: Trusts you completely, Trusts you, neutral, Wary, Stopped listening. Scales lifts from talks and promises (x0.4 to x1.4). |
| Morale | `scripts/sim/ClubLife.gd` (514) | Flat 5..100 per player, 70 settled. Shown as Flying, Settled, Flat, Unhappy. Moves match form by +/-3% and re-sign asks by 25%. |
| Club culture | `scripts/sim/Culture.gd` (462), `scripts/ui/CultureSection.gd` | Standards, Togetherness, Ambition per club, stored in the same `relations` map as `k:<club>:<strand>`. Moves from results, list age, discipline, new faces, broken promises. |
| Promises | `scripts/sim/Backing.gd` (291), `GameState` `expects_game`, dev-talk promises, board win promise | Four separate promise types with their own fields and stings. Breaking one costs morale, trust and Togetherness. |
| Story deck | `scripts/sim/StoryDeck.gd` (489), `scripts/sim/StoryEngine.gd` (1,312), `scripts/state/ClubStories.gd` (1,263), `data/stories/*.json` (13 categories, about 134 cards) plus `data/stories/clubs/` (22 club decks) | Picks one card a week (two in big weeks), cooldowns per card, player and category. Cards read saved facts (morale, trust band, contract, discipline, backing). Effect ops: morale, xp, board, trust, rest, sore, loss sting, culture. Flags start arcs. Validator caps every op. |
| Coach arcs | `scripts/sim/CoachArcs.gd` (350), `scripts/state/ClubArcs.gd` (514), `data/arcs/coach_arcs.json` | Multi-season story arcs triggered from real state, delivered as event cards. The closest thing to a stateful narrative engine today. |
| Weekly big call | `scripts/state/BigCalls.gd` (127) | The Hub's one pressing decision: press, staff approach, captaincy, backing a kid. |
| Staff | `scripts/sim/Coaches.gd` (388), `CoachEffects.gd` (332), `CoachMarket.gd` (1,215), `CoachPathway.gd`, `scripts/ui/StaffScene.gd`, `CoachSheet.gd` | Six jobs at every club (senior coach, senior assistant, mids, forwards, backs, development). Three skills (Teaching, Tactics, Man-management). Man-managers soften the sting of being dropped. A full off-season job market with sackings and poaching. No personality, loyalty or agenda. |
| Coach identity | `scripts/sim/Archetypes.gd` | Two archetypes per senior coach, one Philosophical: Hardline Disciplinarian, Analytical Tactician, Father Figure, The Gambler. Already the Respect vs Authority axis in the brief. |
| Press | `scripts/sim/MediaConference.gd` (1,083), `PressScene.gd` | Five journalist personalities, standing -2..+2 each, answers move morale and trust with shown odds. |
| Leadership and captaincy | `Leadership.gd` (212), `Captaincy.gd` (269), `CaptaincySheet.gd` | Leadership rating from games, age and years at club (facts only for real players). Captain and two vices at every club. |
| On-field traits | `scripts/sim/Traits.gd` (586) | Up to five earned traits plus Hothead (poor discipline). These are match abilities, not personality. |
| Leaving | `TradeRequests.gd` (85), `Contracts.gd` (967), `Retirement.gd` (104) | Trade requests to go home or get a game. Opinion under 50 can refuse to re-sign. Mood feeds whether a veteran goes around again. |
| Team chemistry | `TeamFamiliarity.gd` (206), `ChemistryMeter.gd` | How long teammates have played together. Not interpersonal. |
| Family | `PlayerRelations.gd`, `FamilyTies.gd`, `FamilyLine.gd` | Brothers and fathers, bio only. The only player-to-player link that exists. |
| UI | `PlayerSheet.gd` (opinion and reasons), `PlayerCondition.gd` (mood), `EventCardView.gd`, `HubScene.gd`, `SelectionScene.gd`, `ListScene.gd`, `StaffScene.gd`, `CultureSection.gd` | Opinion line and its reasons on the profile; mood on the list; cards on the Hub. |


### How state moves today

- **After your match** (`GameState` around line 14,930): board confidence moves; `ClubLife.morale_after_match` gives players who played +4 for a win, +1 for a loss; a fit player left out loses 3 (6 if rated 78+), softened by man-managers, Togetherness and the coach archetype. Then each promise is settled: a broken run, a broken game promise or a broken dev promise each cost morale, trust and Togetherness.
- **Every rival club** gets the same morale rule after the round (`_rival_morale_after_round`), because morale feeds match form.
- **The week's card**: `StoryEngine` picks it, `ClubStories` applies the chosen option's ops. Trust moves only here, in the press and through promises.
- **Match day**: morale is the only relationship value that reaches `MatchSim` (via form), plus quarter-break talks (`BreakTalks.gd`) which scale with man-management and the player's trust.
- **Season end**: culture steps, board verdict, contracts (trust and morale), trade requests, retirement.


### Where the brief's picture differs

The brief calls the current system shallow +/- cards. That is fair for morale (one number, no memory) and for staff (no personality). It understates trust, which already keeps every reason. The real gaps are: no decay, no personality, no ambitions, trust is only towards you, staff are skill numbers, and nothing connects one unhappy player to another.


## Bible and ruling check

**Feature test:** the overhaul deserves to exist. It serves the first pillar (the coach's career as a story), roleplaying (every call is a coach's call with a remembered consequence) and agency (selection and promises carry weight beyond the next match). Its risk is the fourth pillar: an information-heavy system can fail readability and turn into busywork.

The design bible itself does not block it. Six standing rulings in the Director Bible do, and they need to be revisited explicitly so the Director Bible records the new direction instead of contradicting it.

| Standing ruling | What it says | Conflict with the brief | Suggested resolution |
|---|---|---|---|
| #8 (2026-10-05) | Crusader Kings informs character continuity; it does not authorise a relationship framework | The brief is a relationship framework | Overturn, recorded as a new ruling |
| #156 (2026-10-05) | Reject routine intrigue, personality spreadsheets and a new relationship graph | Factions, traits, council politics | Overturn the intrigue and personality parts; keep the graph out (decision 1) |
| #38 RPG-009 caveat (2026-10-06) | Most behaviour stays quiet; no personality dashboard, routine check-ins or relationship tending | A Club Politics screen and weekly dilemmas | Keep the spirit: situations surface only when something happened; no tending chores |
| #106 (personality types) | Deferred stretch goal; before design, map against traits, mood, trust, promises, captaincy and cards | Personality traits | This blueprint is that mapping; it needs your go |
| #107 | Persistent promises and player leans were floated, not endorsed | Promises and ambitions are core | Endorse them now |
| Copy voice #38 (2026-11-10) | One coach voice on every screen, no signed staff lines | Council advisors pitching advice | Decide whether advisors may speak in their own voice (decision 5) |

Rulings the plan keeps as they stand:

- **Every club gets it** (2026-11-09): rival players have opinions, personalities, ambitions and factions under the same rules, or it becomes a hidden edge for one side.
- **Never say which option is best**: an advisor's pitch states its upside and cost, it is never labelled the right answer.
- **No invented scandal for a real-named player** (2026-10-11), and a real player gets no invented character judgement (the Leadership rule). This shapes how personalities are assigned (decision 3).
- **Effects must follow from the story** (ruling #9): no opinion drop that a footballer would not actually feel.
- **What the coach decides can affect the sim**: the overhaul reaches the match only through morale and existing levers, measured with `tools/balance.sh match 1000`.


## Proposed data model

Follow the codebase's own pattern rather than introducing Godot `Resource` classes: authored definitions in JSON under `data/relations/`, checked by a validator the way `StoryDeck` checks cards; static rule classes in `scripts/sim/`; runtime state as plain dictionaries in `GameState.relations`, saved with the career. Resources would add a second save format and break the old-save rule (a missing key means neutral).


### Authored definitions (data)

| File | Holds | Example entry |
|---|---|---|
| `data/relations/modifiers.json` | Every opinion modifier: value, decay, grievance tag, words | `dropped_finals`: -30, fades 2 a week, tag `selection`, "Dropped for a final" |
| `data/relations/temperaments.json` | Personality types: how each reacts to each tag, which ambitions it favours, how readily it joins a faction | `mercenary`: contract tags x1.5, club loyalty tags x0.5, favours `extension` |
| `data/relations/ambitions.json` | What a player can want, how it is met, how long he waits | `senior_spot`: 6 of the next 8 games; waits 8 weeks |
| `data/relations/agendas.json` | What a staff member pushes for | `youth`: wants kids picked; loyalty rises when you back one |
| `data/relations/factions.json` | Faction kinds, who joins, pressure thresholds, demands | `fringe`: players outside the best 22 with `selection` grievances |


### Runtime classes and state

| Class (new or grown) | State it owns | Shape |
|---|---|---|
| `Opinion.gd` (grows out of `Trust.gd`, same API kept) | `relations["p:<id>"]` | `{t, mods: [{k, v, y, w, fade, tag, src}], log}`. Opinion = base `t` + live modifiers. `t` stays the permanent part (broken promises); `mods` carry the fading part. `Trust.change` keeps working as a permanent modifier, so the existing call sites in GameState, ClubStories and the press need no edit. |
| `Temperament.gd` | `p["temper"]` | One or two keys per player. Multiplies modifier values by tag; read-only after it is assigned. Named Temperament, not Trait, because `Traits.gd` already means on-field abilities. |
| `Ambitions.gd` | `p["ambition"]` | One active ambition: `{k, since, target, progress, state}`. States: active, met, soured, dropped. Soured feeds a grievance and, at the end, the existing trade request. |
| `Promises.gd` (unifies Backing, `expects_game`, dev-talk promises) | `p["promises"]` plus the coach's record in `gs.coach_word` | `{k, terms, made, due, state, witnesses}`. Keeping or breaking one adds a modifier to him and a smaller one to every player who watched (same line, same faction, the leadership group). |
| `Council.gd` | Grows the existing coach records in `gs.coaches[cid]` | Adds `agenda` and loyalty to you, stored as `relations["s:<cid>"]` (the same Opinion shape). Players attached to him are derived from his job (forwards coach and the forwards, development coach and the kids), not stored. |
| `Factions.gd` | `gs.factions[club]` | `{k, members, leader, grievance, pressure, since, demand, state}`. Formed when enough members share a grievance tag below an opinion line; pressure rises each week the grievance stands; states: forming, active, demanding, ultimatum, settled, broken. |

Everything above lives at every club. Rival clubs run the same rules each round; you only see their results through league news and club pages, never their hidden numbers.


## Integration hooks

The rule: relationships reach the match only through morale, which already moves form by +/-3% in `MatchSim.fit`. `MatchSim`, `Ratings` and `Traits` get no new inputs, so a balance screen compares like with like.

| Hook | Where it plugs in | What it does |
|---|---|---|
| After your match | The block in `GameState` that today runs `morale_after_match` and settles promises | One call, `Relations.after_match(gs, result, played)`. Adds selection modifiers (dropped, dropped for a final, rival picked ahead), settles every promise through `Promises`, moves ambition progress. Replaces the inline promise code. |
| After every round, all clubs | Beside `_rival_morale_after_round` and `_familiarity_after_round` | `Relations.round_tick(gs, club)`: fades modifiers, checks ambitions, recomputes faction pressure. Same code for your club and every rival. |
| Morale | `ClubLife.morale` | Morale stays the one number the match reads. It drifts towards a target set by opinion of you, ambition state and faction membership, instead of moving only by fixed amounts. |
| Selection gate | `SelectionScene.gd` | Read only. Leaving a fit player out shows what it will cost him in opinion and who else will notice, as a number, before you confirm. Nothing applies until the match is played. |
| Story deck | `StoryDeck` conditions and ops, `StoryEngine` picking | New conditions: temperament, ambition state, faction state, staff agenda, opinion band. New ops: add a modifier, make a promise, set or meet an ambition, move faction pressure, move staff loyalty. A faction's demand or an ultimatum comes in as an arc beat, so it uses the arc machinery that already never stalls. |
| Council advice | Card options | An option may carry `pitched_by`: the staff member whose agenda it suits. Taking it lifts his loyalty, passing it over lowers it. Each option still states its upside and cost. |
| Staff moves | `CoachMarket` (sack, poach, hire), `StaffScene` | Sacking or losing a coach adds a modifier to the players attached to him. |
| Contracts and trades | `Contracts.refuse_chance`, `TradeRequests` | Opinion already feeds refusal; temperament scales it. A soured ambition can become a trade request at season end. |
| Save | `GameState` save and load | New keys only, all defaulting to neutral. Needs the W7 lifecycle review (save schema, season rollover, player identity). |

Cost to watch: 18 clubs of about 44 players each get a round tick. Fading modifiers is a loop over short lists, but faction checks should only run when an opinion crossed a line that round.


## Phased plan

Five phases in a straight run, each one shippable and playable on its own. Two changes from the brief's order: promises move into Phase 1 because four promise types already exist and need unifying before anything builds on them, and UI ships inside every phase, because the rule that stored facts must reach a screen (ruling #110) means a system nobody can see is not done.

Every phase exits the same way: `tools/run_tests.sh` green, a real-tap check on each new touch flow, a paired `tools/balance.sh match 1000` table in the PR, a W7 lifecycle review for save changes, and your playtest.

- **Phase 1: Opinion, temperament, bonds, promises and coach standing** (in build, five threads)
  - `Opinion.gd` grown out of `Trust.gd` (Trust stays as its older name): a permanent part plus fading tagged marks from `data/relations/modifiers.json`. Old saves load unchanged.
  - Left-out, star left-out, finals snub and picked-for-a-final marks at every club after each round; morale drifts one point a round towards a target set by opinion (55 to 85).
  - `Temperament.gd`: 8 temperaments, 1 or 2 per player, every player in the league, real and generated.
  - `Bonds.gd`: a sparse map of mates, rivals, mentors, leadership allies and family; dropping, trading or backing a player reaches them.
  - `Promises.gd` unifies Backing, game promises and dev-talk promises; live Respect and Authority for every senior coach, biased by archetype at the start.
  - UI: opinion breakdown, temperament and bonds on the profile; the drop preview on selection.

- **Phase 2: Ambitions**
  - One active ambition per player from facts; met or soured ambitions add marks; soured ones can end in a trade request. First ambition cards.

- **Phase 3: The Council (eight seats)**
  - The six coaching jobs plus List Manager and Head of High Performance, as real jobs at all 18 clubs in `CoachMarket`.
  - Agendas, loyalty, players attached to each coach; advisors pitch in their own signed voice on dilemmas and the weekly call; overruling builds Authority and costs loyalty.

- **Phase 4: Factions**
  - Forming, pressure, demands and ultimatums as arc beats, effects only through morale and Togetherness.

- **Phase 5: Narrative deck overhaul and the Club Politics screen**
  - A full audit of the 134 cards and 22 club decks (started early, read-only, in its own thread), rewrites to read the new state, retiring pure stat-adders, and new dilemmas for every temperament, ambition, faction kind and Council agenda.
  - The Club Politics / Inner Circle screen: Council loyalties, cliques and bonds, active factions and coach standing. Surfaced only through real events, never a weekly chore.


The main risk across all phases is busywork: a weekly chore of keeping people happy. The guard is that nothing asks for attention unless something happened, and the measured interruption rate (cards and alerts a week) is reported in every PR.


## Decisions locked 2026-11-26

The director's answers, which replace the recommendations that were here. Rules 5.169 to 5.177 in the Director Bible hold his exact words.

| # | Decision | Locked answer |
|---|---|---|
| 1 | Who holds opinions of whom | A sparse player-to-player bond map: close mates, bitter rivals, mentor and protege, leadership allies, family. Dropping, trading or backing a player reaches them |
| 2 | What fades | Standard marks fade weekly towards 0; kept and broken promises, finals snubs and deep betrayals are permanent or long-tail |
| 3 | Temperament for real-named players | Every player gets one, real and generated, grounded in footy and locker-room personality; no invented off-field scandal for real people |
| 4 | How many temperaments | Eight: clubman, mercenary, competitor, mercurial, professional, fiery, leader, quiet achiever; 1 or 2 each |
| 5 | How the Council speaks | In their own signed voice and personality, on dilemmas and weekly calls |
| 6 | Council seats | Eight: the six coaching jobs plus List Manager and Head of High Performance, at all 18 clubs |
| 7 | Respect vs Authority | Live Respect and Authority scores moved by your decisions; the archetype sets the starting bias |
| 8 | How much is shown | Exact marks, bond links, weeks left and Respect and Authority effects on the profile and the selection preview |
| 9 | Club Politics screen | A first-class Club Politics / Inner Circle view, without weekly busywork |

Guardrails kept: plain dictionary state with safe old-save defaults, 18-club parity, no mindless weekly chores, and `MatchSim` reached only through form and morale, checked with `tools/balance.sh`.

