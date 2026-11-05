# Culture effects: size review (row 68, T5.Q7)

2026-11-06. Measurement only: no number was changed. Sizes live in `data/culture_effects.json`;
`GameState.culture_effect` reads them, and the same rule applies at every club.

## The numbers

| Strand | Band (value) | Where it acts | Size in the table | What that means in play | How often it fires |
|---|---|---|---|---|---|
| Standards | elite (≥40) / good (≥12) | `Workload.advance_week` recovery multiplier | +5% / +3% | Base recovery is about 17 load points a week (10 + durability×0.10). Elite: +0.85 a week, good: +0.5. The load carries over at 0.75 a week, so the long-run load ends 4× lower: elite −3.4, good −2.0 points out of 100 | Every week, every player at the club, once the band is reached |
| Standards | loose (≤−12) / slack (≤−35) | same | −3% / −5% | +2.0 / +3.4 points of long-run load | same |
| Togetherness | very / tight | `ClubLife.morale_after_match`, a fit player left out | +0.20 / +0.10 softening | A normal player loses 3 morale when left out, a star (78+) 6. Tight (0.10): 3→3 and 6→5. Very (0.20): 3→2 and 6→5. **With rounding, tight changes nothing for a normal player** | Every match, for each fit player left out (about 20 a club a round) |
| Togetherness | cliques / split | same | −0.10 / −0.20 | Cliques: 3→3 and 6→7. Split: 3→4 and 6→7. **Cliques changes nothing for a normal player** | same |
| Ambition | all in / now | `Contracts` re-sign floor (`culture_resign_discount`) | 2% / 1% off his lowest price | On a $600k lowest: $12k / $6k cheaper | Each re-signing at the club |
| Ambition | all in / now | `Contracts.offer_score` for free agents | +0.10 / +0.05 score | The salary scale is 9 points per $1.095M, so +0.10 is worth about $12k a year and +0.05 about $6k | Each free-agent offer from the club |
| Ambition | patient / rebuild | match XP for under-22s and first-season draftees (`GameState._club_xp`) | +3% / +5% | A full senior game is 37 XP: +1 / +2 XP a game after rounding | Every game, young players only |
| Ambition | patient / rebuild | season training ceiling (`season_ceiling`) | +1 point | One more rating point of room a season, inside potential. In practice this is the effect that counts: the season ceiling (+3 a season) otherwise caps the extra XP | Once a season, young players only |
| Any | mid (−11 to +11) | none | 0 | none | every club starts here |

## How strands move (how often a band is reached)

Steps are capped at 6. Each season every strand settles 12% back toward 0. Togetherness: ±3 for runs
of 4/8 losses or 5/10 wins, +3 finals, +5 premiers, −3 bottom four, ±3/−4 list churn, −2 a broken
promise. Standards and Ambition move only at season end: ±4 for discipline or age that stands out
from the league. So reaching *good*/*now* (12) takes about three seasons of the same fact, and
*elite*/*all in* (40) takes about ten, longer once settling is counted. Settling at 40 costs 5 a
season, more than the +4 a season can add, **so Standards and Ambition can almost never reach the
top or bottom band without story choices.**

## Seeded run (GitHub `audit.yml`, `culture_effects_impl`, MEL, 4 seasons, effects on vs off)

| Arm | Seed | Your club's injuries a season (on / off) | Your morale (on / off) | Young rating gain a season (on / off) | League win spread (on / off) |
|---|---|---|---|---|---|
| Natural culture | 1 | n/a | league 69.40 / 69.20 | n/a | 4.58 / 4.55 |
| Forced elite, very tight, rebuild | 1 | 15.5 / 16.75 | 64.06 / 64.13 | **3.88 / 2.94** | 4.33 / 4.55 |
| Forced slack, split, all in | 2 | 21.5 / 22.25 | 63.21 / 65.72 | 2.99 / 2.94 | 4.30 / 4.63 |

Run ids: 42033795575, 42033800961, 42033806386, 42033811515, 42033817597, 42033823595.

What it shows:
- **Rebuild's young growth is the only effect big enough to see**: about +0.9 rating a season for
  each young player (+1 ceiling point, as intended).
- Standards and Togetherness are lost in noise at this sample size. Split/slack cost 2.5 morale and
  had no effect on injuries. Elite/very tight had no effect on morale and 1.25 fewer injuries a season.
- Natural culture: in seed 1 no club reached *now*/*all in* in 4 seasons, so the free-agent and
  re-sign effects never fired. Seed 2: 5% of clubs got there, and they took 5% of free agents (6% off).
- No snowball: the top third by culture against the bottom third, next-season wins, were lower with
  effects on (4.78 on against 6.33 off; 2.00 against 4.50).

Not exercised: one seed per arm and 4 seasons. The forced elite/very/rebuild "on" arm stopped
after 2 seasons (the bot was sacked). The audit only uses bot selection, so man-manager softening is
not part of it. The "off" arms had 4 seasons. Treat these as signs, not a calibration.

## Questions for the director

1. Tight and cliques do nothing for a normal player because 3 × 0.9 and 3 × 1.1 both round to 3.
   Is that acceptable as "small", or should the band still be felt?
2. Standards and Ambition top bands can hardly be reached through play (settling beats the +4 a
   season). Do you want them reachable?
