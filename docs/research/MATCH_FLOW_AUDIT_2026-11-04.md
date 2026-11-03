# Match flow audit, 2026-11-04 (TODO row 11)

Switch: `match_flow` (default off, `Features.gd`). Off, a match is draw-for-draw as on main. On: a ball-up comes from a
contest that locks up (a held tackle, a rushed kick into a pack, a spoil in the pocket), never from a won ball; after an
intercept or a free the winner plays on; chains are shorter and more numerous (`Ratings.FLOW`: 275 chains, 10 touches).

Method: `tools/audit/shape_impl.gd`, 400 matches, the calibration sample (real 2026 lists, seed 1234 + i), on GitHub's
runner (audit.yml runs 41673484719 off, 41673380897 on, branch `claude/row11-match-flow`, `SHAPE_FLOW=1` for on).
Real = Champion Data 2026 per team a game (Wheelo, 436 team-games). Balance is the director's call; these are numbers.

| Team a game | Off | On | Real | On / real |
|---|---|---|---|---|
| Disposals | 364.0 | 353.5 | 367.5 | 0.96 |
| Marks | 95.7 | 95.5 | 91.7 | 1.04 |
| Tackles | 58.4 | 57.2 | 57.4 | 1.00 |
| Inside 50s | 51.8 | 51.1 | 53.1 | 0.96 |
| Clearances | 38.3 | 39.5 | 36.2 | 1.09 |
| Hitouts | 36.6 | 37.7 | 35.8 | 1.05 |
| Clangers | 52.9 | 54.5 | 55.9 | 0.97 |
| Frees for | 17.6 | 19.0 | 18.7 | 1.02 |
| Goals | 13.0 | 12.9 | 12.9 | 1.00 |
| Behinds | 9.8 | 10.1 | 9.5 | 1.07 |
| Contested possessions | 88.1 | 118.1 | 129.3 | 0.91 (off 0.68) |
| Intercepts | 52.0 | 66.0 | 65.4 | 1.01 (off 0.80) |
| Intercept marks | 9.4 | 11.0 | 14.4 | 0.76 (off 0.65) |
| Spoils | 17.3 | 17.5 | 30.8 | 0.57 (off 0.56) |
| Ground ball gets | 40.7 | 61.7 | 86.5 | 0.71 (off 0.47) |
| Ruck contests (all stoppages) | 94.0 | 97.0 | ~91 | 1.07 |

Points a team a game: 88.0 off, 87.4 on. Still short with the switch on: spoils (0.57), intercept marks (0.76), ground
ball gets (0.71). Row 11 is partly met: the calibrated stats are within 9% of real, but those three are not at real, so the bands do not all hold. Intercepts (1.01) are reached partly by definition: a tackle that spills free and a pocket ball-up are both booked as possessions won (a spill counts as an intercept; a pocket ball-up counts as an effective entry, and the spoiling defender gets no rebound). The calibration suite still guards the off path.
