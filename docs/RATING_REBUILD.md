# Player rating rebuild (approved 2026-11-25)

The director's rulings are Director Bible rule 4.2.30a; this file is the approved blueprint with his five
amendments written in. Where this file and the bible disagree, the bible wins.

## 0. Earlier rulings replaced

| Earlier ruling | Replaced by |
|---|---|
| 11-15 rulings 2 and 20: skills and OVR rated against his AFL position | One league-wide scale (mandate 2) |
| 11-15 ruling 2: OVR = official AFL Player Rating | OVR worked out from attributes (mandate 3); real players' OVRs will move |
| 11-15 ruling 10: Goalkicking = goals a game | Finishing becomes **Goalkicking**; goals a game moves to **Forward craft** |
| 11-17: past-peak take-back of 40-100% | Age curves for each attribute (§4), applied a little each round |
| `data/ovr_overrides.csv` (23 rows) | Deleted, not converted. The POT override rows stay. |
| 11-15 "No invented stats", for speed only | Speed estimate for players with no GPS record (§2): position base plus a bounces and pressure bump, capped at 68 |
| Calibration (15 team stats within ±7% of real AFL) | Goes red when the data changes in Phase 4; the sim is retuned. Balance stays his call. |

## 1. Teardown list

**Files deleted**
- `data/engine_scale.csv`, `tools/wheelo/engine_scale.py`, `tools/wheelo/engine_targets.csv` (Phase 4).
- `tools/wheelo/fit.py`, `fit_copy_pool.gd`, `copy_pool.py`, `data/copy_pool.csv` (Phase 3).
- `tools/wheelo/weights_pre2012.json`, `weights_report.py` (Phase 3).
- `data/ovr_overrides.csv`, `data/rating_stats_2026.csv` (replaced by `data/attributes_2026.csv`) (Phase 3/4).
- The rating mirror in `tools/sim_harness.py`; its 5 importers re-pointed (Phase 8).

**Code removed**
- `Skills.gd` whole (`engine`, `_load_scale`, `migrate`), replaced by `Attributes.gd`.
- `Prospects`: `fit_attributes`, `UNRATED_KEYS`, `project` (RANK_BANDS, readiness), copy-pool shaping.
- `Ratings.gd`: `derive_all`, `METRIC_SPECS`, `ATTR_BLENDS`, `ROLE_BLENDS`, `rate_on_record/honours/rehab`,
  `HONOURS_*`, `ROLE_WEIGHTS`, `LINE_FIT`, `rate_overall`, `overall_per_point`, `ATTR_ADJUSTMENTS`,
  `ROLE_CORRECTIONS`. Team selection stays, re-pointed.
- `GameDB`: `_load_rating_stats`, `_apply_rating_stats`, `set_player_ovr`, `_rate_few_games`, `baseline_overall`.
- `GameState`: `_recompute_ratings` and the `season_start_ov` bookkeeping.
- `Potential`: `outlook`, `reachable_peak`, `AGE_HEADROOM`, `ROLE_CAP`. `assign` stays.
- `Growth`: OVR-point pricing and OVR breakouts (rebuilt on attributes), the dead `over_gains`.
- `MatchSim`: the `STAR_OVR` read of stored OVR (uses derived OVR). `Squad`: the `team_star` term.

**Player and save fields removed:** `overall`, `value`, `rates`, `norm`, `role_scores`, `attr_unrecorded`,
`season_start_ov`, `baseline_overall`.

## 2. Attributes: 18, 1-99, one scale for every position

**Scale.** Rate stats: the league's 2nd percentile is 1, its 98th is 99. Per-game counts: zero is 1, the 98th
percentile 99. A stat a season does not record is left out. Height and weight stay as measured body facts.

| Group | Attribute | Real-player recipe (Wheelo) | What it drives in the match |
|---|---|---|---|
| Physical | Speed | GPS top speed, 32.5 km/h = 70 up to 36.0+ km/h = 98 (`C:/kt/speed`); no GPS, a combine 20 m time: 2.80 s = 90 up to 3.10 s = 50; neither: estimate (below) | Open-field separation, line-breaking runs, chase-down tackles (tackling 20%) |
| | Endurance | Time on ground | How fast he tires (`MatchSim:5844`, `Workload:61`); tackling 20% |
| | Strength | Weight for height 50 + contested possessions a game 50 | Breaking tackles, one-on-one and ruck contests |
| | Work Rate | Pressure acts 30 + bounces 25 + (inside 50s + rebound 50s) 25 + uncontested possessions 20, against what his position, height and weight usually produce | Transition spread, uncontested link-up chains, repeat defensive pressure |
| Technical | Kicking | Efficiency 50 + metres gained per kick 50 | Kick range, ball use, disposal (56%) |
| | Handballing | Efficiency 60 + handball metres gained 40 | Holding the ball, disposal (44%) |
| | Marking | Uncontested marks a game | Marks off kicks, kick-or-handball choice |
| | Contested marking | Contested marks 50 + attacking one-on-one win % 50 | Attacking side of aerial contests |
| | One-on-one defence | Defensive one-on-one loss % (inverted) 50 + spoils 30 + one-percenters 20 | Spoils, defending packs and leads |
| | Contested ball | CP 30 + ground ball gets 20 + clearances 35 + CP rate 15 | Clearances, centre attendances, wet fumbles |
| | Goalkicking | xScore rating per shot from 2021, goals per shot before | Whether the shot goes in |
| | Ruck | Hitouts 35 + to advantage 30 + win % 20 + ruck clearances 15 | Hitouts |
| Footy IQ | Vision | Goal assists 40 + score involvements 25 + launches 15 + inside 50s 20 | Inside-50 delivery, setting up shots |
| | Reading the play | Intercept possessions a game | Intercepts, roaming, back-half ball use |
| | Pressure | Pressure acts 70 + tackles 30 | Tackling 60%, zone pressure, minders |
| | Forward craft | Goals a game 50 + marks inside 50 30 + marks on the lead 20 | Which forward is the danger and gets the shot |
| Mental and durability | Discipline | Frees against 70 + clangers 30 (inverted) | Clangers, frees, 50s, reports |
| | Durability | Share of club games played | Injury chance (`Injuries:45`), soreness |

**Dropped:** `star` (OVR's job; Squad's contest composite becomes 0.48 mid contest, 0.27 ruck, 0.25 mid
disposal), `carry` (its reads go to Speed and Work Rate), `accuracy` (now Goalkicking). Endurance stays: Work Rate
and time on ground correlate only 0.20 across 2026, so the card grows to 18 (director, 2026-11-25: "Keep **both**
**Speed** and **Work Rate**").

**Speed, Strength and Work Rate (director, 2026-11-25, locked: "Stop overcomplicating the regressions and stop
asking tuning micro-questions").** Speed with a GPS record: the straight line above, his best record. Without one:
Small (Gen Def, Gen Fwd) 62, Mid (Mid, Mid-Fwd) 56, Key (KD, KF) 45, Ruck 32, plus 0 to +10 from bounces and pressure
acts a game, capped at 68 so no estimate passes a measured sprinter; no height penalty; his card marks it estimated.
Strength: weight for height is his weight against the list's line for his height (84.2 kg at 188 cm, +0.89 kg a cm),
2nd percentile 1, 98th 99. Work Rate: the blend's residual after position, height and weight (least squares over
12+ game players), 2nd percentile 1, 98th 99; handball receives are in none of our data. Uncontested possessions =
contested possessions x (100 - CP rate) / CP rate. A combine 20 m time with no GPS (132 listed players): a straight
line, 2.80 s = 90 and 3.10 s = 50, whatever his position (director, question box). Speed records spell clubs as a
code, a name or not at all: a name two listed players share matches only a record whose club is his.

**In-match modifiers:** fitness (energy ×0.80-1.05), form, wet weather, opponent pressure, and out of
position (new). **Out of position (amendment):** cuts Footy IQ and Technical attributes only, never Speed,
Strength or Endurance (nor Work Rate, a Physical attribute, nor Discipline or Durability); the cut grows with
positional distance. Sizes (director, question box): 5% a step along KD, GD, Mid, Mid-Fwd, Gen Fwd, KF, at most 25%;
into or out of the ruck 25%; except KD to KF or KF to KD (swingman) 10%, and KD or KF moved to Mid 20%. Each
Technical and Footy IQ attribute plays at (1 - cut) while he is there.

| From \ to | KD | GD | Mid | Mid-Fwd | Gen Fwd | KF | Ruck |
|---|---|---|---|---|---|---|---|
| KD | 0 | 5 | 20 | 15 | 20 | 10 | 25 |
| GD | 5 | 0 | 5 | 10 | 15 | 20 | 25 |
| Mid | 10 | 5 | 0 | 5 | 10 | 15 | 25 |
| Mid-Fwd | 15 | 10 | 5 | 0 | 5 | 10 | 25 |
| Gen Fwd | 20 | 15 | 10 | 5 | 0 | 5 | 25 |
| KF | 10 | 20 | 20 | 10 | 5 | 0 | 25 |
| Ruck | 25 | 25 | 25 | 25 | 25 | 25 | 0 |

## 3. Derived positional OVR

OVR(player, position) = Σ weight × attribute ÷ 100, rounded; his primary position or the slot's. Worked out
when shown or used, never saved, never fed back. Durability weighs 0 (priced in Worth instead). Work Rate has no starting weight; Phase 4 measures one.

| Attribute | KD | GD | Mid | Mid-Fwd | Gen Fwd | KF | Ruck |
|---|---|---|---|---|---|---|---|
| Speed | 5 | 10 | 6 | 8 | 10 | | |
| Endurance | 4 | 6 | 10 | 5 | 4 | 4 | 8 |
| Strength | 10 | | 6 | | | 10 | 12 |
| Kicking | 8 | 15 | 12 | 10 | 5 | 5 | |
| Handballing | 3 | 7 | 12 | 6 | | | 5 |
| Marking | 5 | 10 | 4 | 6 | 10 | 10 | |
| Contested marking | 15 | 5 | | | 5 | 25 | 10 |
| One-on-one defence | 25 | 12 | | | | | |
| Contested ball | | | 22 | 12 | | | 15 |
| Goalkicking | | | 3 | 12 | 18 | 20 | |
| Ruck | | | | | | | 40 |
| Vision | | 4 | 10 | 12 | 10 | | |
| Reading the play | 15 | 18 | | | | | |
| Pressure | 5 | 8 | 12 | 12 | 14 | 4 | 5 |
| Forward craft | | | | 14 | 20 | 18 | |
| Discipline | 5 | 5 | 3 | 3 | 4 | 4 | 5 |
| Work Rate | | | | | | | |

These are starting numbers. Phase 4 measures them: per position, +10 on one attribute for every player there,
1,000 paired matches; the margin each attribute buys becomes its weight; the measured table goes to him in `REVIEW.md`
before it is locked. Best OVRs are expected in the 80s; Phase 8 recalibrates colour cuts and grades so mid-80s
reads as elite.

## 4. Generation, progression, economy

**Draftees.** One of the 12 types each. Ranges: each attribute's 10th-90th percentile among real
first-season players of that type, aged 18-20, Wheelo 2012-25. A draftee draws a talent percentile, takes his
type's ranges at it, ±6 noise; POT from talent plus noise (`Potential.assign`). The Forge, expansion lists,
depth pools and state leagues use the same ranges.

**Progression.** XP (2/3 matches, 1/3 training, VFL half) buys attribute points; the plan picks which; a point
costs more the higher the attribute. No gains once derived OVR at his primary position reaches POT (11-23).
Age curves a little each round: Endurance, Durability, technical and Footy IQ measured year on year in Wheelo
2012-25; Discipline XP only. Speed (grows to 23, holds to 26, −1.5 a season from 27, −3 from 31) and Strength
(grows to 26, holds to 31, −1 a season from 32) were decision 8, not named in his reply: *ask before Phase 7.*
Breakouts: same rate, +4 to +6 on his three most heavily weighted attributes. Types retested each season.

**Economy.** Worth = 0.50 × OVR at his best position + 0.20 × Form + 0.30 × POT − 1.5 a year past 29, with a
**Durability factor (amendment)** so injury-prone players take a contract and trade discount. *Its form and
size open: ask before Phase 5.* Form = last 10 `MatchNotes.match_rating` against his position's league
average, on the OVR scale; under 5 games, Form = OVR.

| Consumer | Uses |
|---|---|
| Contracts | Asking salary from Worth |
| Trades | (Worth ÷ 70)^5 |
| Draft ranking | OVR·(1−w) + POT·w (w 0.25 and 0.65), from fogged attributes |
| AI selection | Best 0.8 × OVR at the slot + 0.2 × Form; ruck and key posts by position OVR |
| Scouting blur | ±6 per attribute at full uncertainty, scout tiers ×1.25/1.00/0.80/0.65; shown OVR from fogged attributes |

## 5. Phases (each its own PR, green CI, auto-merge)

Director, 2026-11-25: "Fold Phase 2 into Phase 4—skip any temporary bridges or backward-compatibility
detours." "i dont care about old saves": no save upgrader, no frozen curves; a career saved before Phase 4 does not
load after it. Lists and weight tables for his review go in `REVIEW.md` at the repo root (gitignored).

| # | What lands | Proof |
|---|---|---|
| 1 | `Attributes.gd` (one list, groups, labels) replaces the 6 copies; `Rating.ovr(p)` wraps the OVR reads (still returns stored OVR) | Suites green; paired balance zero change |
| 2 | Folded into 4 (director, 2026-11-25) | |
| 3 | Wheelo rewritten for 18 attributes, league-wide: `attributes_2026.csv` (`tools/wheelo/attributes.py`); fitters, copy pool, weights, `rating_stats`, `ovr_overrides` deleted; 2027 lists in `REVIEW.md` | His read of the lists |
| 4 | The swap: 18 attributes load on one league-wide scale (`engine_scale.csv` and `Skills.engine` deleted), sim reads them directly, out-of-position cut, OVR derived and dropped from saves, sim retuned, weights measured (table in `REVIEW.md`) | Calibration, balance table, his playtest |
| 5 | Economy and AI: Worth with Durability, contracts, trades, draft ranking, selection, blur | Draft, contract, trade suites |
| 6 | Generation: type ranges, classes, Forge, expansion, depth pools, state leagues | Intake and Forge-on-every-start tests |
| 7 | Progression: XP into attributes, POT cap, age curves, breakouts, trait retest | Multi-season audit |
| 8 | UI and words: card in four groups, colour cuts, grades, PlaysLike, Roles, story thresholds; `.hist` careers regenerated | Real taps; captures to him |
