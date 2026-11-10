# Coaches build a plan: one strength, one cost

_Research for rows 40 and 41 (own game plan builder), 2026-11-10, main @ 88ea5634. Options and trade-offs only: nothing here
is a recommendation, and neither row is assigned. Code paths are relative to the repo root._

A custom plan with one bespoke strength and one matching cost fits the engine with little new plumbing. A plan is already
a small dictionary of multipliers over nine levers (`MatchSim.PLANS`, read through `_pv`). The closest shipped
precedents are the Strategic coach archetypes (row 119), which every rival coach also carries, and Club Forge's
compulsory weakness (#989). The hard parts are elsewhere. The oval only knows plans by name, so a new plan draws as
Balanced until its strength and cost map to a shape that clears the 8 m floor. The press side effects are hard-coded,
so any custom "press" strength quietly becomes part of a Defensive Press. The counter triangle has no slot for a plan
that changes from club to club. And two rulings are still open: what the director meant by "3 for our club forge, but 1
for our game as is", and whether the feature belongs in the base game at all. Other games show the same pattern. A
small menu of named pairs is measurable and patchable. Free-form builders breed one copied meta (FM24) or "slider soup"
(OOTP). And a cost only works if it bites the builds that pick it.

## 1. How the game works now

### Five plans, nine levers, one accessor

There are five plans: Balanced, Attack Corridor (`attacking`), Defensive Press (`defensive`), Win Contest (`contest`) and
Controlled Tempo (`controlled`) ([CoachReport.gd:10-16](../../scripts/sim/CoachReport.gd)). Each non-Balanced plan is a
dict in `MatchSim.PLANS` ([MatchSim.gd:930-943](../../scripts/sim/MatchSim.gd)). It draws on nine keys: `goal` (your
conversion), `opp_goal` (theirs), `exposed` (theirs, meant for turnovers), `gain` (metres per disposal), `clangers`,
`press` (pressure you apply), `taken` (pressure you absorb), `contest` (additive stoppage win chance) and `pace` (how
hard the legs work) (glossary at [MatchSim.gd:920-927](../../scripts/sim/MatchSim.gd)).

| Plan | Upside keys (scaled) | Cost keys (fixed) |
| --- | --- | --- |
| Attack Corridor | goal 1.05, gain 1.06 | clangers 1.12, pace 1.12, exposed 1.07 |
| Defensive Press | press 1.09, opp_goal 0.965 | goal 0.88, gain 0.95, pace 1.12 |
| Win Contest | contest +0.025 | gain 0.95, exposed 1.04 |
| Controlled Tempo | taken 0.96, clangers 0.93, goal 1.01, pace 0.95 | gain 0.94 |

`_pv(side, key)` ([MatchSim.gd:959-979](../../scripts/sim/MatchSim.gd)) scales only the upside keys (`PLAN_UPSIDE`).
The scale is coach execution × list fit (`PlanFit`, clamp 0.45-1.55, [PlanFit.gd:17-46, 110-116](../../scripts/sim/PlanFit.gd))
× weather (`WEATHER_PLAN`, e.g. wet: contest 1.35, attacking 0.6, [MatchSim.gd:946-956](../../scripts/sim/MatchSim.gd))
× drilling (well 1.0 / partly 0.95 / barely 0.9, [PreSeason.gd:61, 630, 676](../../scripts/sim/PreSeason.gd)). A
Strategic archetype multiplies both upside and cost while its own plan is on. Costs are otherwise never scaled. This
matches the open gate M1, "list fit, coaching, weather scale the gain, never the cost"
([DECISION_TRANSPARENCY_RULINGS_2026-11-03.md](DECISION_TRANSPARENCY_RULINGS_2026-11-03.md)).

Where the levers bite: press at [982-1000, 3274](../../scripts/sim/MatchSim.gd) (zone-shaped by
`PRESS_PLAN_ZONE [1.40, 1.10, 0.60]`), taken [3281], gain [3413], conversion [4131-4148], clangers [4506-4508],
contest [1651, 1659-1660] (still under the contest clamp) and pace [4913-4916] (GPS and fatigue). Every lever credits its
points to a cause through `_credit()`. That cause feeds the full-time "what your calls were worth" lines
([CoachReport.gd:104-115](../../scripts/sim/CoachReport.gd)), so a custom plan riding the `gameplan` cause is attributed
at no extra cost.

### Hard-coded behaviour a custom plan would inherit

The **press side effects** trigger whenever `_pv(opp,"press") > 1.0`. They are back-third turnovers ×1.5
([3362-3363](../../scripts/sim/MatchSim.gd)), a broken press setting `_broke_press` and that chain's shot ×1.7 likelier
a goal ([3427-3430, 4145-4146](../../scripts/sim/MatchSim.gd)), the press halving an Attack Corridor's goal edge
([4133-4134](../../scripts/sim/MatchSim.gd)), and Bring the heat stacking only half on a press
([1700-1706](../../scripts/sim/MatchSim.gd)). The **counter triangle** is hard-coded too. Controlled holds off a press
as far as its fit allows, Attack Corridor feels the press ×1.10 ([995-999](../../scripts/sim/MatchSim.gd)), and
Controlled shooters ignore `opp_goal`/`exposed` ([4139-4143](../../scripts/sim/MatchSim.gd)). The AI's
`COUNTER := {controlled: attacking, defensive: controlled, attacking: defensive}` ([6108](../../scripts/sim/MatchSim.gd))
has no entry for Balanced or Win Contest. One engine quirk matters for any "exposed" cost: `exposed` is applied to every
shot, not only turnover chains (from the read of 4131-4148).

The nearest existing per-side hook is the archetype lever dict `arch[side]`, read by `_ar(side, key)`
([1013-1017, 470](../../scripts/sim/MatchSim.gd)). It already multiplies taken, gain, goal, exposed, clangers, legs
(fatigue only), fifty, injuries and morale. It does not reach press, opp_goal, contest or pace (movement); those exist
only through `_pv`.

### Short calls

`BURSTS` holds Stack the stoppage (12 chains), Flood behind the ball (45, rest of the quarter), Throw numbers at it (15)
and Slow it down (15) ([5243-5252](../../scripts/sim/MatchSim.gd)). Each uses named constants such as STACK_CONTEST
0.10, FLOOD_OPP_GOAL 0.80, FLOOD_GOAL 0.90 and BACK_GAIN 0.85 ([5255-5273](../../scripts/sim/MatchSim.gd)), consumed by
hard-coded `_burst()` branches. Only Stack and Flood are offered today, on the run-of-goals and late-Q4-bounce moment
cards ([5296-5353, 5435-5450](../../scripts/sim/MatchSim.gd)). No live card was found for Throw numbers or Slow it down.
Their gate copy carries sized percentages through `GateOdds.burst_lines` ([GateOdds.gd:28-47, 100-124](../../scripts/sim/GateOdds.gd)),
e.g. Flood: "their shots 20% less accurate" against "your shots 10% less accurate, 15% less ground a kick".

### Who picks the plan

You set a standing plan on the Coaching hub (`GameState.CLUB_PLANS`, `set_club_plan()`,
[GameState.gd:12988-13004](../../scripts/state/GameState.gd)) and can change it before the bounce and at every break
([MatchScene.gd:954](../../scripts/ui/MatchScene.gd)). The assistant never changes it ([MatchSim.gd:868-882](../../scripts/sim/MatchSim.gd)).
A rival's "usual plan" is settled at round 1 from `PlanFit.standing_plan`. It plays a real plan only when its list is 0.4
spreads above the league, otherwise Balanced ([GameState.gd:4095-4114](../../scripts/state/GameState.gd),
[PlanFit.gd:118-131](../../scripts/sim/PlanFit.gd)). Each quarter it may switch by scoreboard mood, or from Q2 counter
the plan you showed last quarter, never one it hasn't seen ([6087-6205](../../scripts/sim/MatchSim.gd)).

Coach archetypes ([Archetypes.gd:24-50, 282-296](../../scripts/sim/Archetypes.gd), PR #1243) are the shipped precedent
for a bespoke plan strength with a cost. Each Strategic archetype amplifies one plan's upside and cost ×1.5.
Territory's cost was doubled to 2.0 because at 1.5 it measured +3.8 points a match. All 12 arms of 1,000 paired matches
then sat inside the noise, and every rival coach carries an archetype from his own skills.

### The oval: MatchDirector shapes (#784, #1282)

`MatchDirector` reads the sim's per-side timeline (`plan`, `bursts`) and bends each token's spot with plan-specific
branches ([MatchDirector.gd:111-115, 2196-2332, 2631-2641](../../scripts/ui/match/MatchDirector.gd)). PR #784 (f930a0f2)
gave every plan and short call a shape:

- **Corridor:** lanes (ATTACK_SHARE 0.4, LANE_GAP 7, drawn band CORRIDOR_HALF 14.25).
- **Press:** band (PRESS_LAST_LINE 46, PRESS_NARROW 0.62, plus a camera nudge).
- **Controlled:** width (CONTROL_WIDTH 1.5).
- **Contest:** ring plus one extra man in every pack.
- **Short calls:** surge pushes, hold depth.
- **Tempo:** `CALL_PACE` attacking 1.15, controlled 0.85.

PR #1282 (d78cf903, today) lifted Flood from 5.5 m and Stack from 2.8 m to the floor. It also added
`tools/visual/capture_calls.gd`, which films each call against Balanced on the same events. The floor is
`CALL_FLOOR := 8.0` in `_test_call_visibility` ([tests/test_match_motion.gd:31, 554-561](../../tests/test_match_motion.gd)).
Shapes are bound to plan ids by string match, so an unknown plan id draws as Balanced.

### Club Forge's compulsory weakness (#989, row 80): it lives in Create a player

The weakness rule is in Club Forge > **Create a player**, not Create a club. `scripts/sim/ClubForge.gd` has no plan,
strength or weakness. You pick up to two strengths and must pick one weakness (a second is optional)
([Prospects.gd:821-858](../../scripts/sim/Prospects.gd)). Each strength adds +7 and each weakness takes −7, then
`fit_attributes` refits him to the same overall: "no choice buys power" ([Prospects.gd:808-811, 925-948](../../scripts/sim/Prospects.gd),
commit aa895df2). For a plan, the matching discipline is net margin ≈ 0 on paired seeds, as the archetypes were
measured. Created clubs enter "like every club" under identical rules (DIRECTOR_BIBLE.md:616, 1713).

### TODO rows and rulings

- **TODO C, row 40/41** ([TODO.md:47](../TODO.md)): "Own game plan builder (game as is; Club Forge): decision waits on
  his plan-drilling play." Drilling has shipped, so the blocker is his play, not code.
- **TODO F41** ([TODO.md:63](../TODO.md)): "Club Forge game-plan builder." The original 2026-10-13 row: "A full
  game-plan builder for the Club Forge ... design sheet first" (git 32665e75).
- **Section Z** ([TODO.md:207, 226](../TODO.md)): no balance tune until every other row is done. The paired 1,000-match
  screen before a PR still applies ([TODO.md:74](../TODO.md)). There are no feature switches (2026-11-06).
- **DB 2.55** ([DIRECTOR_BIBLE.md:274](../DIRECTOR_BIBLE.md)): "i love the idea of 3 for our club forge, but 1 for our
  game as is". **DB 159** (:894): own plan in the game as is is open, a stretch, 1.x. Open questions **13** (:369) and
  **61** (:2317) ask whether it belongs in the base game, the Forge, or neither.
- **DB 2.54** (:272): "One plan description per plan, no percentages", carried into the `PLAN_PARTS` comment
  ([CoachReport.gd:34](../../scripts/sim/CoachReport.gd)).
- **Parity and trade-off rulings:**
  - AI is never psychic and has no hidden advantages (:83, entry 24 near :1670).
  - Same rules for every club (:551, :572, :1672).
  - Every option names its trade-off (2.64 :294, 31 :420, 15 :703).
  - "Avoid arbitrary large stat buffs" (:848); "permanent coach buffs" excluded (:700, :751).
  - Balance-gated changes need 1,000+ seeded matches per condition (:1647).
  - A feature that never fires is a bug (:2397).

**A conflict to correct, not a question.** DB 2.54 and the `PLAN_PARTS` comment say plan descriptions carry no
percentages. Design bible principle 4 (2026-10-18) and the 2026-11-10 transparency ruling 2 ("Gain for this list
today") say every gate shows size and odds as percentages. The bible wins. The 2.54 line and the CoachReport comment
should be corrected whenever plan copy is next touched. A custom plan's gate must print its gain and cost as
percentages for this list today.

## 2. How other games do it

**The pattern works when the cost forces a commitment.** Slay the Spire's boss relics pair a strong effect with a real
downside, so the player has to "define your deck"
([design analysis](https://saschb2b.github.io/game-mechanics/games/slay-the-spire/design-tensions);
[Steam discussion](https://steamcommunity.com/app/646570/discussions/0/1742232339939829970)). Darkest Dungeon pairs
quirks on the same stat without mirroring them exactly (+15% bleed resist against −10%), and both halves are named
([wiki](https://darkestdungeon.wiki.gg/wiki/Quirk)). Path of Exile designed a keystone that gives nothing to builds
already capped, so its value depends on the build ([forum](https://pathofexile.com/forum/view-thread/2549575)).

**It fails in three recurring ways.**

- **The cost doesn't bite.** If most builds never feel the cost, the pick is strictly better. Players say an extra
  energy every other turn helps almost any deck.
- **The pick is untakeable.** If the cost outweighs the gain for nearly everyone, nobody takes it (Runic Pyramid
  complaints, same Steam thread).
- **A whole category drifts.** TFT had to tune trait augments up because they "struggled compared to their more
  versatile peers" ([11.24](https://teamfighttactics.leagueoflegends.com/en-gb/news/game-updates/teamfight-tactics-patch-11-24-notes/)).
  Later it made "a very large balance pass" nerfing econ augments
  ([17.5](https://teamfighttactics.leagueoflegends.com/en-us/news/game-updates/teamfight-tactics-patch-17-5)).

The drift can come from the cost side as well. EA reduced College Football 25's Wear and Tear accrual within two months
of launch ([Dexerto](https://dexerto.com/gaming/college-football-25-september-19-update-patch-notes-wear-tear-recruiting-2904638)).
Madden's staff abilities exist "to cover a head coach's weak spots"
([ESPN](https://africa.espn.com/gaming/story/_/id/45708826/madden-nfl-26-franchise-mode)). That is the warning case
here: any system that can erase the debuff erases the trade-off.

**Free-form builders breed a meta.** In FM24 "basically every single player" in a creators' league ran the same
press-heavy 4-3-3, which was banned along with a FIFAe-winning gegenpress
([VideoGamer](https://www.videogamer.com/?p=1182667)). Some players run "1000s of test[s] to exploit the match engine"
([FM Scout](https://www.fmscout.com/q-34468-Same-tactics-works-every-time.html)). SI's answer in FM26 kept choice but
guided it:

- a style first, with suggested out-of-possession shapes;
- staff who "flag that your approach carries risk";
- a pitch visualiser showing the shape by third
  ([FM26](https://www.footballmanager.com/fm26/features/possession-out-possession-fm26s-new-tactical-evolution)).

FM27 adds in-match tweaks, with staff advising "when to stop using one"
([FM27](https://www.footballmanager.com/node/1108)). FM shows trade-offs with stars and warnings, almost never numbers.
That makes it a model for drawing the shape on the pitch, not for the gate. OOTP's layered strategy sliders and manager
preferences leave users unsure which setting wins ([OOTP forums](https://forums.ootpdevelopments.com/showthread.php?p=2785565)).

**AFL games show the cost of hidden effects.** AFL 26 offers "a lengthy list of possible strategic options"
([Press Start](https://press-start.com.au/reviews/ps5-reviews/2025/05/11/afl-26-review-a-solid-iteration/)). Reviewers
found it hard to tell how management choices change a season
([Player2](https://www.player2.net.au/2025/06/afl-26-review-premiers-arent-made-in-may/)). That is bible principle 3
failing in this exact niche.

**Sirlin's rules.** Avoid any dominant move. Give every strong option a counter. Make options different enough that
their value is hard to compare. Cut choices nobody should pick ("chaff"). Playtest, because theory does not substitute
([Part 2](https://sirlin.net/articles/balancing-multiplayer-games-part-2-viable-options)). Read across to this game,
each strength should be a different football identity, not +X% variants of one stat. The rival answering from Q2 is
the counter. Plans locked before the bounce are the double-blind.

## 3. Real AFL archetypes and what each cost

| Archetype (club, coach) | Strength | Cost | Lever mapping | Source |
| --- | --- | --- | --- | --- |
| Defensive zone (St Kilda, Fremantle, Lyon) | Ranked 1st for defence in 2009, 2010, 2013, 2023 | Attack ranked 4th, 8th, 12th, 15th; three GFs lost; called "physically and mentally taxing" | opp_goal down / goal down (+pace) | [ESPN](https://africa.espn.com/afl/story/_/id/40140827/afl-ross-lyon-st-kilda-saints-defensive-gameplan-hindering-development) |
| Clarko's Cluster (Hawthorn 2008) | Fewest inside 50s conceded; 2008 flag | Solved within a season: 9th in 2009, dropped by 2010; concedes boundary ball | opp gain down / own gain down (decays) | [AFL.com.au](https://www.afl.com.au/news/113924/credit-clarko); [Wikipedia](https://en.Wikipedia.com/wiki/Alistair_Clarkson) |
| Kick-mark possession (Hawthorn 2013-15) | Kept the ball best; won 26 of 37 games while losing contested possession | Beaten at its own game: Essendon won uncontested marks 128-76 | taken/clangers down / contest down | [The Roar](https://www.theroar.com.au/2016/04/29/cares-flags-hawks-need-win-contested-possessions/amp/); [AFL.com.au](https://www.afl.com.au/news/71694/bombers-beat-hawks-at-their-own-game-clarkson) |
| Flood (Sydney 2005, Roos) | 2005 flag, the club's first in 72 years | Low, short-chip scoring; called "disgusting" by commentators (looks never touch the sim) | opp_goal down / goal and gain down | [Wikipedia](https://www.wikipedia.org/wiki/Paul%20Roos%20(Australian%20rules%20footballer)) |
| Chaos ball (Richmond 2017-20) | 1st for intercepts and tackles inside 50 in 2017 | Needs sustained pressure (later lowest rating in nine years); answered by denying ground-ball gets | press up / pace up, contested marks down | [SEN](https://archive.sen.com.au/news/2018/09/10/richmonds-chaos-game-and-how-its-made-them-so-dominant/index.html); [AFL.com.au](https://www.afl.com.au/news/1094791/pressure-down-tigers-appetite-for-the-fight-plummets/amp) |
| Forward press (Collingwood 2010, Malthouse) | Forward-50 tackling to goals; 3rd for tackles at mid-season | **Unsourced:** exposed to long kicks over the top | press up / exposed up | [Collingwood FC](https://www.collingwoodfc.com.au/news/753035/mid-season-stat-review) |
| Intercept defence (Melbourne 2021) | Fewest points conceded; Lever 1st for intercept possessions (10.3); flag 140-66 | **Unsourced:** zoning talls leave leading forwards free | new hook: intercept marks / free leads | [Melbourne FC](https://www.melbournefc.com.au/news/1025963/21-season-jake-lever); [AFL.com.au](https://www.afl.com.au/news/682099/dee-fence-the-secret-weapon-in-melbournes-drought-breaking-season) |
| Contest and pressure (GWS 2023, Kingsley) | Clearance diff 13th to 2nd; pressure 9th to 3rd | **Unsourced:** stoppage-heavy games suppress scoring | contest up / gain down | [AFL.com.au](https://www.afl.com.au/news/1030979/big-big-turnaround-how-greater-western-sydney-giants-rebounded-to-become-flag-threat) |
| Attack-first (Brisbane 2026, Fagan) | Scored 114.8 a final; third straight flag | Conceded 110.8 a final, the most by any premier | goal and gain up / exposed and opp_goal up | [AFL.com.au](https://www.afl.com.au/news/1624541/way-of-the-future-or-once-off-brisbane-lions-set-extraordinary-mark-in-flag-run) |
| Risk-taking ball movement (Collingwood, McRae) | "if you don't have a throw at the stumps, you never run anyone out" | **Unsourced:** turnover-prone ball movement | gain up / clangers up | [AAP](https://aapnews.aap.com.au/news/injury-concerns-won-t-stop-magpies-taking-risks-coach) |
| Run-and-carry handball (Geelong 2007-11) | **Unsourced:** fast corridor, flags 2007, 2009, 2011 | **Unsourced:** concedes on the rebound when the chain breaks | gain and pace up / exposed up | none |
| Contested midfield (Brisbane 2001-03, Matthews) | **Unsourced:** dominant clearances, three flags | **Unsourced:** none recorded | contest up / pace | none |

**Correction.** Collingwood **won** the 2023 grand final, beating Brisbane. A search tool's summary in the notes said
otherwise. The notes gathered no source for the game style behind that flag.

Two football-true observations bear on equal options. All 24 premiers since 2000 ranked top six for defence, and 21 of
them also ranked top six for attack (ESPN, above). One-dimensional styles have a measured ceiling. Second, Brisbane and
Fremantle met in the 2026 GF as attack-first against best-defence, each carrying the other's weakness (AFL.com.au,
above). Opposite identities can both reach the last day, which is the "options equal" target in real life. Champion
Data's 2026 game descriptors (transition/stagnant, high/low pressure, contested/uncontested, central/boundary) are a
ready vocabulary of axes ([ESPN](https://africa.espn.com/afl/story/_/id/47924207/afl-stats-champion-data-2026-new-statistics-speed-ball-movement-last-touch-rule)).

## 4. Design options

Rulings apply to every option, and none is asked again. Every rival club gets the same feature by the same rules
(CLAUDE.md, 2026-11-09; DB :83, :572). Options must be equal, with none better on the scoreboard. The gate shows upside,
downside, size and odds in football words with percentages. What the coach decides can affect the sim, and the oval
must change visibly.

Every option shares the balance method. Screen with `tools/balance.sh match 1000`, paired seeds. Today
`--side-plan X` and `--coach S,P` force one side, and `side_compare.py` gives that side's paired margin
([balance_body.gd:120-136](../../tools/balance/balance_body.gd)). Each option needs a proposed
`--custom-plan key=+x,key=-y` arm arg mirroring `--side-plan`, compared against `--side-plan balanced`. A pair passes
when |B−A| < 2 se, the archetype standard. Any tune past the first screen waits in TODO section Z. `side_compare.py`
would need pressure acts, turnovers, intercepts and distance run added for press or pace pairs.

### Option A: two cards from the existing levers

**What the coach sees.** On the Coaching hub, "Build our own plan" sits beside the four stock plans. The coach picks one
strength card and one cost card, each a football sentence with its size. Strength cards: "Win it back high", "Tighter
on their shots", "Kick it further", "Better shots at goal", "Win more stoppages", "Keep the ball", "Hold up under
pressure". Cost cards: "Heavier legs", "Shakier kicking", "Shorter kicks", "Rushed shots", "Exposed on the rebound",
"Give them better looks". He names the plan, and it joins the break picker.

- **Menu version.** Each card has a fixed size, set so that any legal pair nets ≈ 0 on paired seeds. Some pairs are
  barred: a strength and cost on the same lever, or ones that cancel.
- **Free-form version.** The coach sets the strength's size on a short dial (small, medium, big). The cost grows to
  match from a measured exchange rate, like #989's refit to the same overall. The gate shows both percentages live.

**Hooks.** A custom plan is a new plan id whose dict holds two keys. Its strength goes in `PLAN_UPSIDE`, so `_pv` scales
it by fit, execution, weather and drilling, and the cost stays fixed. The plan id would need adding to:

- `PlanFit.NEEDS` (fit taken from the strength's lever, e.g. press to the pressure players);
- `PreSeason.DRILL_PLANS`;
- `WEATHER_PLAN` (weather inherited from the stock plan sharing the strength's lever);
- `CoachReport.PLAN_NAMES/PLAN_PARTS` (with sized lines from GateOdds-style templates);
- `GameState.CLUB_PLANS`.

A save field is needed for each club's custom dict. A "Win it back high" strength (press > 1.0) trips all three press
side effects. Either its card carries them as part of its named cost ("space behind if they break it"), or the gate is
changed to key on the stock plan id. Counter triangle: a custom plan sits outside it, as Balanced and Win Contest do.
Alternatively it inherits the triangle slot of its strength's lever (press → beaten by Controlled), which the AI could
then counter from Q2 having seen it. No archetype amplifies it unless `Archetypes.PLAN` maps its strength lever.

**The oval.** Each strength card maps to an existing shape: press to the press band, gain to corridor lanes, contest to
the ring and +1 pack, taken/clangers to Controlled width, opp_goal to the flood fold. Pace scales `CALL_PACE`. The cost
draws nothing of its own; it shows in the feed and the full-time "what your calls were worth". The composed shape must
clear CALL_FLOOR 8 m against Balanced in `capture_calls.gd` for every strength card.

**Rivals.** Each rival builds one at round 1 by the same rule. The strength is its best `PlanFit`-style attribute group
and the cost its weakest. It plays the result as its usual plan when the fit clears the same 0.4-spread bar, copying
`standing_plan`. Its card names are scoutable, like `THEIR_PLAN`.

**Balance.** One `--custom-plan` arm per legal pair: with about 7 × 6 cards, roughly 35-40 arms of 1,000. That is
about 85 s each on the local harness, or run on GitHub runners. Free-form adds one arm per dial step to fit the
exchange rate.

**Feature test.** Serves player agency and roleplay: the coach's own identity on the oval. Understandable, because two
named cards in football words sit inside the existing plan vocabulary. Risk to the bible: with ~40 pairs, some will sit
outside the noise (Sirlin's dominant move, TFT's drift). The free-form dial reopens FM-style optimisation.

### Option B: lean a stock plan

**What the coach sees.** He starts from one of the four stock plans and makes it his own. He pushes one of its
strengths harder and accepts one extra cost from a short list, e.g. "Our Defensive Press: hunt higher (+press), and
the legs pay more (+pace)". The plan keeps its name with a suffix ("Defensive Press, our way").

- **Menu version.** Each stock plan offers two or three fixed leans, each a strength-up and cost-up pair.
- **Free-form version.** Any of the plan's upside keys can be pushed and any key outside it taken as the cost, with the
  size refit to net ≈ 0.

**Hooks.** The smallest change. It is a per-side lever dict multiplied in where `_pv` reads that stock plan, or written
through `arch[side]` / `_ar` for the six keys `_ar` already reaches (taken, gain, goal, exposed, clangers, legs).
Press, opp_goal, contest and pace need a small `_ar` hook at [990, 1660, 4142, 4913]. Fit, drilling, weather, counter
triangle, AI counters and the press side effects all stay with the stock plan unchanged. Strategic archetypes already
amplify their plan, so a lean stacks with them. That stack is the riskiest arm to measure, as Territory at 1.5 was.

**The oval.** The stock plan's shape stays and the lean scales one of its constants (PRESS_LAST_LINE deeper,
LANE_SPACE wider, CONTEST_PACK +1). The difference from the stock plan must also clear 8 m, or the lean is invisible.
That is the hard part: #1282 showed 3-6 m changes do not read.

**Rivals.** Rivals lean their usual plan by the same rule, the lean matching their strongest attribute for that plan.
The rival read shows the lean once it has been seen.

**Balance.** Four plans × 2-3 leans, about 8-12 arms, each also run stacked with that plan's archetype.

**Feature test.** Serves agency and readability. It is the restraint answer: nothing new to learn and few arms to
measure. Weakness against the feature test: it is a refinement, not a new identity. Whether it meets "his very own game
plan" is the director's reading.

### Option C: AFL identities, named and adopted

**What the coach sees.** A short shelf of real styles from section 3, written as football, not as stats. "The zone:
they won't find the corridor; we won't score much either." "Chaos ball: bring it to ground and swarm; we lose the big
marks inside 50." "Kick-mark: keep it and pick them apart; we lose the hard ball." "Attack at all costs: we score, they
score." He adopts one, names it, and it becomes his club's plan.

- **Menu version.** Five or six fixed identities, each with one strength and one cost already paired, sized and
  measured.
- **Free-form version.** The identity is fixed; the coach sets only how far to commit (lean in, all in), with
  strength and cost scaling together.

**Hooks.** Each identity is a curated two-key dict on the nine levers: zone = opp_goal ↓ / goal ↓; chaos ball = press ↑
/ contested marks ↓ (needs a new hook) or press ↑ / pace ↑; kick-mark = taken and clangers ↓ / contest ↓; attack =
goal and gain ↑ / exposed and opp_goal ↑. Some overlap stock plans: attack ≈ Corridor, zone ≈ Flood. Each identity
needs a defined relation to the stock plans (a replacement, or a sixth-plus plan) and a counter-triangle slot written
by hand, as Sirlin's counters-of-counters. Identities needing new levers (intercept marks, ground-ball gets) wait for
Option D's hooks or are cut.

**The oval.** Each identity gets its own authored shape, built and captured like #784/#1282. The zone needs a full-ground
web, chaos ball crumbing forwards at the fall of the ball. That is the most art and motion work of any option, with
every shape above 8 m and checked frame by frame before the director sees it.

**Rivals.** Every rival adopts the identity its list fits best (or Balanced below the 0.4-spread bar). A rival
coach's archetype could map to identities as `strategic_for_plan` does.

**Balance.** 5-6 arms (two per identity in free-form), plus each identity against every other on forced sides. This
tests whether opposite styles meet as equals, like Brisbane against Fremantle in 2026.

**Feature test.** Serves immersion and natural AFL language most strongly ("the vision of a realistic sports-RPG",
DB :52). Its pick is a choice among the designer's identities, not the coach's own invention. That cuts against "his
very own game plan" unless the free-form commit dial and naming are enough. The director's reading decides.

### Option D: new football levers for the strength and cost

**What the coach sees.** Option A's two-card pick, with cards that name things the current plans cannot: "Our talls
zone off and take intercept marks; their leading forwards get free." "Set shots from 40 m and in; we give up the
long-range snaps." "Kick-ins go long to the contest; we lose the short switch." "Small forwards crumb at the fall; we
lose the contested mark."

- **Menu version.** A fixed list of new-lever cards, each with a fixed size.
- **Free-form version.** Any new-lever strength with any lever cost, with an exchange-rate dial.

**Hooks.** New sim hooks outside `PLANS`, each with its own `_credit` cause:

- intercept-mark chance by zone (INTERCEPT_EVIDENCE.md exists);
- set-shot share and accuracy by distance (the harness already reports accuracy by distance);
- kick-in choice (ZONE in MatchDirector);
- ground-ball versus marking contest.

Kick lanes (T2.25, plan-weighted corridor/switch, [TODO.md:89](../TODO.md)) is not on main yet. If it lands, it is a
natural lever: corridor ↑ / switch ↓. None of these touch the counter triangle or press side effects unless written to.
This is the most engine work and the most save and test surface.

**The oval.** New shapes: talls dropping off their man into a zone, forwards held inside 40 m for set shots, kick-in
lines. Each needs its own capture against Balanced on the same events and the 8 m floor. Some effects (set-shot
accuracy) are not positional and show only as events and feed copy. That is weaker against "the visual sim changes
greatly".

**Rivals.** The same card rule from list strengths (talls → intercept marks; small forwards → crumbing), observable
and scoutable.

**Balance.** One arm per card pair, plus a league-wide arm for every new hook with no plan active. A new lever must
first leave the existing real-AFL rates IN, through the 62 `BALANCE_CHECKS` thresholds (TODO.md:226).

**Feature test.** Serves agency, football truth and "the game shows what each decision led to". It conflicts with the
earlier research ("do not add a modifier layer when clearer jobs would suffice"; "correct or remove ineffective controls
before adding a new playstyle", AFL_AGENCY_AND_TEAM_BUILDING_RESEARCH.md:31-35, 106). It also conflicts with
restraint. Rows 40/41 do not ask for new levers, so scope is the director's call.

### Option E: the plan as a Club Forge identity (row 41 only)

**What the coach sees.** In Club Forge > Create a club (which has no plan today), the founding coach writes the club's
way of playing. He picks one strength and one cost, by any of A-D's mechanics, and it is that club's plan for the
career. The game as it is keeps only the stock plans. This is one reading of "3 for our club forge, but 1 for our game
as is"; the meaning of 1 and 3 is unrecovered.

- **Menu version.** The club's identity is picked once at creation from fixed pairs.
- **Free-form version.** Strength and cost with an exchange-rate dial, chosen at creation and revisited only at a
  season's end.

**Hooks.** Whatever A-D supply, stored on the created club (`Squad.usual_plan` plus a dict) instead of the coaching
hub. Because the identity is long-lived, drilling (`plan_know`) and list fit matter more. Recruiting to the plan becomes
the coaching fantasy, the EA scheme-fit idea where playbook drives Team Needs
([EA Help](https://help.ea.com/sv/articles/madden-nfl/madden-playbooks-guide)).

**The oval.** Same as the chosen mechanic.

**Rivals.** Created clubs enter "like every club" (DB :616, :1713). For parity, every club in a Forge career also has a
founding identity, generated from its list by the same rule. Otherwise the created club holds a lever no one else has.

**Balance.** As for the chosen mechanic, plus a season-length arm. A permanent identity compounds through list
building, which 1,000 single matches cannot show; it needs a multi-season audit (afl-audit-runs) in section Z.

**Feature test.** Serves roleplay and legacy ("a simulation that feels like a story, a legacy, a dynasty"). It keeps the
base game's plan screen unchanged (restraint). Watch the "permanent coach buffs" exclusion (DB :700, :751): it was
written about media, but a permanent club-wide strength reads close to it unless the cost is equally permanent and
named.

### How the options differ at a glance

| | New identity for the coach | Engine work | Oval work | Arms to screen | Where it lives |
| --- | --- | --- | --- | --- | --- |
| A Two cards | High (~40 pairs) | Medium (new plan id across 6 lists) | Low (reuse shapes) | ~35-40 | Base game |
| B Lean a stock plan | Low | Low | Hard to clear 8 m | ~8-12 (+archetype stacks) | Base game |
| C AFL identities | Medium (designer-curated) | Medium | High (new shapes) | ~5-6 plus head-to-heads | Base game or Forge |
| D New levers | High | High | High | Per card, plus league-wide | Base game or Forge |
| E Forge identity | As chosen | As chosen | As chosen | As chosen, plus seasons | Club Forge |

## 5. Questions for the director

1. **What did "1" and "3" mean?** On 2026-10-13 you said "i love the idea of 3 for our club forge, but 1 for our game
   as is" (DB 2.55). The option list behind 1 and 3 is in neither the repo nor git history. What were options 1 and 3?
2. **Where does it live?** Base game, Club Forge only, both, or neither? (Open DB questions 13 and 61; row 40/41 "waits
   on his plan-drilling play". Drilling has shipped.)
3. **Old levers or new ones?** Are the strength and cost limited to what plans already move (pressure, ground gained,
   accuracy for and against, clangers, stoppages, legs)? Or may they add new football levers such as intercept marks,
   set shots and kick-ins (Option D)?
4. **When can he change it?** Like the stock plans, at the bounce and every break? Or is it set once per season (or at
   club creation) as a club identity?
5. **Does something beat it?** Does a custom plan join the counter triangle, so a stock plan counters it and the rival
   can answer it from Q2? Or does it sit outside the triangle, like Balanced and Win Contest?
6. **How big?** Should a custom strength be stock-plan sized (roughly 2-12% on one lever), or bigger than a stock plan
   with a bigger cost to match?

## Sources

Codebase (main @ 88ea5634):

- `scripts/sim/MatchSim.gd`, `PlanFit.gd`, `PreSeason.gd`, `Archetypes.gd`, `CoachReport.gd`, `GateOdds.gd`, `Prospects.gd`
- `scripts/state/GameState.gd`, `scripts/ui/match/MatchDirector.gd`
- `tests/test_match_motion.gd`, `tools/balance/`
- `docs/TODO.md`, `docs/DIRECTOR_BIBLE.md`, `docs/DESIGN_BIBLE.md`, `docs/research/DECISION_TRANSPARENCY_RULINGS_2026-11-03.md`,
  `LEVER_TRUTH_AUDIT.md`, `AFL_AGENCY_AND_TEAM_BUILDING_RESEARCH.md`, `AFL_MATCH_VISUALISATION_AND_TACTICS_RESEARCH.md`
- PRs #784, #989, #1243, #1282; commit 32665e75

Games:

- [FM26 tactics](https://www.footballmanager.com/fm26/features/possession-out-possession-fm26s-new-tactical-evolution)
- [FM27 tweaks](https://www.footballmanager.com/node/1108)
- [VideoGamer on the FM24 meta](https://www.videogamer.com/?p=1182667)
- [OOTP forums](https://forums.ootpdevelopments.com/showthread.php?p=2785565)
- [ESPN on Madden 26](https://africa.espn.com/gaming/story/_/id/45708826/madden-nfl-26-franchise-mode)
- [Dexerto on CFB25](https://dexerto.com/gaming/college-football-25-september-19-update-patch-notes-wear-tear-recruiting-2904638)
- [Slay the Spire design tensions](https://saschb2b.github.io/game-mechanics/games/slay-the-spire/design-tensions)
- [Darkest Dungeon quirks](https://darkestdungeon.wiki.gg/wiki/Quirk)
- [TFT 11.24](https://teamfighttactics.leagueoflegends.com/en-gb/news/game-updates/teamfight-tactics-patch-11-24-notes/)
- [TFT 17.5](https://teamfighttactics.leagueoflegends.com/en-us/news/game-updates/teamfight-tactics-patch-17-5)
- [Sirlin, viable options](https://sirlin.net/articles/balancing-multiplayer-games-part-2-viable-options)
- [Press Start AFL 26](https://press-start.com.au/reviews/ps5-reviews/2025/05/11/afl-26-review-a-solid-iteration/)

AFL:

- [ESPN on Lyon](https://africa.espn.com/afl/story/_/id/40140827/afl-ross-lyon-st-kilda-saints-defensive-gameplan-hindering-development)
- [AFL.com.au on Clarkson](https://www.afl.com.au/news/113924/credit-clarko)
- [The Roar on Hawthorn](https://www.theroar.com.au/2016/04/29/cares-flags-hawks-need-win-contested-possessions/amp/)
- [SEN on Richmond](https://archive.sen.com.au/news/2018/09/10/richmonds-chaos-game-and-how-its-made-them-so-dominant/index.html)
- [Melbourne FC on Lever](https://www.melbournefc.com.au/news/1025963/21-season-jake-lever)
- [AFL.com.au on GWS](https://www.afl.com.au/news/1030979/big-big-turnaround-how-greater-western-sydney-giants-rebounded-to-become-flag-threat)
- [AFL.com.au on Brisbane 2026](https://www.afl.com.au/news/1624541/way-of-the-future-or-once-off-brisbane-lions-set-extraordinary-mark-in-flag-run)
- [ESPN on Champion Data 2026](https://africa.espn.com/afl/story/_/id/47924207/afl-stats-champion-data-2026-new-statistics-speed-ball-movement-last-touch-rule)
