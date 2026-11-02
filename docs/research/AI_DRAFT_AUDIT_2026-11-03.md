# AI draft audit, 2026-11-03 (roadmap row 37)

Supersedes [draft_strategy_audit_2026-10-12.md](draft_strategy_audit_2026-10-12.md): main changed the National
Draft since (#732, it runs until every list is full), so the old numbers no longer describe the game.

## Headline

- **Do AI-built lists end up weaker than the real 2026 lists?** No. Across 6 seeds x 10 seasons, AI clubs' best 23
  sits **+2.5 OVR (redraft) and +2.6 (real-list start) above the real 2026 lists** at the end of season 10
  (69.73 ± 0.04 and 69.84 ± 0.05 against 67.24). Depth 24-38 ends level with the real lists (-0.17 and +0.04). The
  old audit's depth gap (-0.7 to -1.2) is gone.
- **Do AI clubs draft well pick by pick?** Not as well as they could. Picks 11-30 take a player worth **5.9 points
  below the best left** on the board (true values); picks 1-10, 3.3. Scouting noise explains about 0.5-0.7 of it;
  the rest is scarcity (VORP) and the covered-position mark-down.
- **The buff** (switch `ai_draft_buff`, off): scarcity ramps in over two rounds and is capped at 5 points, and a
  covered position keeps 97% of a prospect's worth (was 92%). It **cuts the pick gap by about 2 worth points at
  picks 1-30** (paired, ± SE: redraft 1-10 -2.05 ± 0.16, 11-30 -1.97 ± 0.25; real 1-10 -1.97 ± 0.09, 11-30
  -1.23 ± 0.30) but **changes list strength by nothing measurable**: best 23 within ±0.06 at every snapshot, squad
  strength within ±0.4 and inside two SE except real-list S10 (-0.42 ± 0.17).
- Reading: since AI lists already beat the real lists, there is no gap for a buff to close. The buff makes rival
  picks look smarter on draft night without making their teams stronger. It ships **off**; turning it on is the
  director's call.
- **Rivals only.** The buff applies only to rival clubs; the user's "Pick for me" keeps the shipped scoring
  (director undecided whether it should change too). The CI runs below predate this guard, so the autopilot user
  club's own picks were buffed in the buff arm; that club is dropped from every end-of-season table, and its
  picks are about 1/18 of the pick-gap rows.

## Paired buff minus base

### redraft: buff minus base, paired by seed (AI clubs, ± SE over seeds)
| Moment | Seeds | Base best 23 | Buff−base best 23 | Base depth 24-38 | Buff−base depth | Base squad strength | Buff−base squad | Buff−base U23 POT |
|---|---|---|---|---|---|---|---|---|
| S1 start | 6 | 67.68 ± 0.01 | +0.00 ± 0.00 | 52.65 ± 0.01 | +0.00 ± 0.00 | 68.73 ± 0.05 | +0.00 ± 0.00 | +0.00 ± 0.00 |
| end S1 | 6 | 69.68 ± 0.05 | +0.00 ± 0.00 | 54.31 ± 0.02 | +0.00 ± 0.00 | 69.61 ± 0.24 | +0.00 ± 0.00 | +0.00 ± 0.00 |
| end S2 | 6 | 70.35 ± 0.05 | -0.02 ± 0.01 | 53.84 ± 0.07 | +0.02 ± 0.03 | 71.32 ± 0.18 | -0.15 ± 0.17 | -0.10 ± 0.10 |
| end S3 | 6 | 69.87 ± 0.06 | -0.00 ± 0.02 | 52.87 ± 0.11 | -0.02 ± 0.14 | 71.15 ± 0.07 | -0.08 ± 0.24 | -0.07 ± 0.20 |
| end S5 | 6 | 70.17 ± 0.05 | -0.06 ± 0.04 | 52.72 ± 0.10 | -0.26 ± 0.10 | 72.19 ± 0.22 | +0.24 ± 0.12 | -0.03 ± 0.16 |
| end S7 | 6 | 69.91 ± 0.06 | +0.05 ± 0.09 | 52.18 ± 0.19 | -0.04 ± 0.31 | 72.23 ± 0.18 | -0.09 ± 0.30 | -0.21 ± 0.21 |
| end S10 | 6 | 69.73 ± 0.04 | +0.05 ± 0.06 | 52.00 ± 0.18 | +0.01 ± 0.23 | 72.38 ± 0.27 | +0.15 ± 0.28 | +0.09 ± 0.18 |

### real: buff minus base, paired by seed (AI clubs, ± SE over seeds)
| Moment | Seeds | Base best 23 | Buff−base best 23 | Base depth 24-38 | Buff−base depth | Base squad strength | Buff−base squad | Buff−base U23 POT |
|---|---|---|---|---|---|---|---|---|
| S1 start | 6 | 67.71 ± 0.00 | +0.00 ± 0.00 | 53.46 ± 0.00 | +0.00 ± 0.00 | 68.89 ± 0.03 | -0.10 ± 0.03 | -0.01 ± 0.00 |
| end S1 | 6 | 69.88 ± 0.03 | +0.01 ± 0.01 | 55.23 ± 0.02 | -0.04 ± 0.03 | 70.20 ± 0.17 | -0.05 ± 0.05 | -0.01 ± 0.02 |
| end S2 | 6 | 70.83 ± 0.04 | +0.02 ± 0.05 | 54.57 ± 0.04 | -0.04 ± 0.04 | 72.38 ± 0.18 | -0.07 ± 0.19 | -0.06 ± 0.08 |
| end S3 | 6 | 70.12 ± 0.03 | -0.02 ± 0.01 | 53.16 ± 0.12 | -0.07 ± 0.16 | 72.04 ± 0.18 | -0.16 ± 0.30 | -0.01 ± 0.08 |
| end S5 | 6 | 70.25 ± 0.04 | +0.02 ± 0.07 | 52.61 ± 0.16 | +0.06 ± 0.12 | 72.76 ± 0.28 | +0.37 ± 0.28 | -0.11 ± 0.22 |
| end S7 | 6 | 70.06 ± 0.04 | +0.05 ± 0.08 | 52.32 ± 0.12 | +0.16 ± 0.09 | 72.67 ± 0.16 | +0.14 ± 0.16 | +0.15 ± 0.30 |
| end S10 | 6 | 69.84 ± 0.05 | +0.00 ± 0.03 | 52.21 ± 0.19 | -0.06 ± 0.23 | 72.90 ± 0.12 | -0.42 ± 0.17 | -0.01 ± 0.29 |

### National Draft picks: worth gap to the best player left (true values), paired by seed
| Careers | Pick band | Base gap | Buff gap | Buff−base |
|---|---|---|---|---|
| redraft | 1-10 | 3.39 ± 0.15 | 1.33 ± 0.06 | -2.05 ± 0.16 |
| redraft | 11-30 | 5.90 ± 0.29 | 3.93 ± 0.14 | -1.97 ± 0.25 |
| redraft | 31-60 | 4.22 ± 0.26 | 4.27 ± 0.26 | +0.05 ± 0.33 |
| real | 1-10 | 3.27 ± 0.06 | 1.30 ± 0.04 | -1.97 ± 0.09 |
| real | 11-30 | 5.82 ± 0.26 | 4.59 ± 0.11 | -1.23 ± 0.30 |
| real | 31-60 | 5.15 ± 0.30 | 5.13 ± 0.22 | -0.02 ± 0.46 |

## Base audit tables (switch off), from `tools/audit/draft_strategy_agg.py`

## Seeds and user clubs
real 11: MEL, real 12: COL, real 13: ADE, real 14: CAR, real 15: GEE, real 16: SYD, redraft 11: MEL, redraft 12: COL, redraft 13: ADE, redraft 14: CAR, redraft 15: GEE, redraft 16: SYD

### A. Real lists, pre-draft 2026 lists (mean over 6 run(s))
| Club | List | Best 23 | Depth 24-38 | Under 23 | 23-29 | 30+ | U23 POT | Squad strength |
|---|---|---|---|---|---|---|---|---|
| ADE | 36 | 69.1 | 52.5 | 8 | 24 | 4 | 68.5 | 69.8 |
| BRL | 39 | 67.4 | 52.7 | 11 | 19 | 9 | 74.4 | 66.9 |
| CAR | 37 | 68.7 | 53.4 | 12 | 16 | 9 | 73.5 | 70.4 |
| COL | 40 | 70.1 | 52.7 | 11 | 17 | 12 | 68.7 | 71.9 |
| ESS | 39 | 62.0 | 50.9 | 19 | 18 | 2 | 71.0 | 60.2 |
| FRE | 39 | 69.2 | 53.3 | 10 | 24 | 5 | 67.1 | 70.9 |
| GCS | 42 | 67.0 | 51.4 | 15 | 20 | 7 | 72.6 | 67.9 |
| GEE | 40 | 70.3 | 55.0 | 11 | 20 | 9 | 71.5 | 70.3 |
| GWS | 39 | 67.3 | 51.5 | 20 | 15 | 4 | 68.8 | 67.7 |
| HAW | 38 | 70.6 | 52.9 | 11 | 19 | 8 | 71.1 | 69.3 |
| MEL | 38 | 67.0 | 50.9 | 15 | 16 | 7 | 70.5 | 68.9 |
| NTH | 39 | 68.3 | 51.9 | 17 | 17 | 5 | 72.2 | 68.7 |
| PAD | 37 | 64.8 | 49.6 | 12 | 22 | 3 | 69.3 | 66.0 |
| RIC | 37 | 62.2 | 50.0 | 16 | 16 | 5 | 71.4 | 64.6 |
| STK | 39 | 66.1 | 51.9 | 15 | 17 | 7 | 71.3 | 66.7 |
| SYD | 40 | 68.5 | 54.2 | 12 | 20 | 8 | 68.5 | 68.9 |
| WBD | 39 | 67.0 | 50.7 | 14 | 22 | 3 | 70.7 | 71.9 |
| WCE | 49 | 64.7 | 53.7 | 25 | 20 | 4 | 68.6 | 64.7 |
| **League mean** | 39 | 67.2 | 52.2 | 14 | 19 | 6 | 70.5 | 68.1 |
| **Spread (SD across clubs)** | 2.8 | 2.52 | 1.47 | 4.2 | 2.7 | 2.7 | 1.95 | 2.95 |

### A. Real lists, season-1 start (mean over 6 run(s))
| Club | List | Best 23 | Depth 24-38 | Under 23 | 23-29 | 30+ | U23 POT | Squad strength |
|---|---|---|---|---|---|---|---|---|
| ADE | 39 | 69.3 | 54.0 | 11 | 24 | 4 | 69.5 | 71.3 |
| BRL | 41 | 67.6 | 53.8 | 13 | 19 | 9 | 74.6 | 67.2 |
| CAR | 40 | 69.0 | 54.8 | 15 | 16 | 9 | 74.1 | 70.4 |
| COL | 43 | 70.5 | 54.1 | 14 | 17 | 12 | 70.0 | 72.2 |
| ESS | 43 | 63.0 | 52.4 | 23 | 18 | 2 | 71.6 | 63.0 |
| FRE | 41 | 69.4 | 54.0 | 12 | 24 | 5 | 68.3 | 71.1 |
| GCS | 44 | 67.5 | 52.2 | 17 | 20 | 7 | 73.4 | 69.9 |
| GEE | 42 | 70.5 | 55.8 | 13 | 20 | 9 | 72.4 | 70.4 |
| GWS | 42 | 67.8 | 53.2 | 23 | 15 | 4 | 69.7 | 68.8 |
| HAW | 40 | 70.7 | 54.4 | 13 | 19 | 8 | 71.9 | 69.4 |
| MEL | 41 | 67.6 | 52.3 | 18 | 16 | 7 | 71.0 | 69.1 |
| NTH | 43 | 69.0 | 53.6 | 21 | 17 | 5 | 72.3 | 70.1 |
| PAD | 41 | 65.8 | 51.3 | 16 | 22 | 3 | 70.4 | 67.6 |
| RIC | 41 | 63.2 | 51.8 | 20 | 16 | 5 | 72.1 | 65.7 |
| STK | 42 | 66.7 | 53.2 | 18 | 17 | 7 | 71.8 | 68.0 |
| SYD | 42 | 68.8 | 55.3 | 14 | 20 | 8 | 69.9 | 69.2 |
| WBD | 42 | 67.6 | 52.5 | 17 | 22 | 3 | 71.2 | 72.1 |
| WCE | 49 | 64.7 | 53.7 | 25 | 20 | 4 | 68.6 | 64.7 |
| **League mean** | 42 | 67.7 | 53.5 | 17 | 19 | 6 | 71.3 | 68.9 |
| **Spread (SD across clubs)** | 2.1 | 2.32 | 1.23 | 4.1 | 2.7 | 2.7 | 1.78 | 2.52 |

Baseline used for the gaps: real pre 2026. Best 23 67.24, depth 52.17, U23 POT 70.53, squad strength 68.08; SD of best 23 across clubs 2.52; best-worst club 8.6.

### B. Redraft careers: AI clubs, league mean over seeds (+/- standard error), gap to the real 2026 lists (A)
| Moment | Seeds | List size | Best 23 | Gap to A | Depth 24-38 | Gap to A | Depth 24-32 | Gap to A | U23 POT | Gap to A | Squad strength | Gap to A | U23 count | 30+ count | SD of best 23 across clubs | Best-worst club |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 start | 6 | 40.00 ± 0.00 | 67.68 ± 0.01 | +0.44 | 52.65 ± 0.01 | +0.47 | 54.10 ± 0.02 | +0.33 | 71.02 ± 0.73 | +0.49 | 68.73 ± 0.05 | +0.65 | 13.33 ± 0.00 | 7.06 ± 0.00 | 1.21 ± 0.16 | 4.2 |
| end S1 | 6 | 36.04 ± 0.09 | 69.68 ± 0.05 | +2.45 | 54.31 ± 0.02 | +2.14 | 55.52 ± 0.03 | +1.74 | 70.92 ± 0.74 | +0.39 | 69.61 ± 0.24 | +1.53 | 13.07 ± 0.20 | 5.43 ± 0.05 | 1.40 ± 0.11 | 5.6 |
| end S2 | 6 | 33.51 ± 0.13 | 70.35 ± 0.05 | +3.12 | 53.84 ± 0.07 | +1.67 | 54.52 ± 0.10 | +0.74 | 72.37 ± 0.25 | +1.84 | 71.32 ± 0.18 | +3.24 | 10.94 ± 0.15 | 5.66 ± 0.05 | 1.85 ± 0.05 | 8.0 |
| end S3 | 6 | 32.27 ± 0.04 | 69.87 ± 0.06 | +2.63 | 52.87 ± 0.11 | +0.70 | 53.03 ± 0.10 | -0.74 | 70.20 ± 0.13 | -0.34 | 71.15 ± 0.07 | +3.07 | 10.57 ± 0.16 | 5.93 ± 0.14 | 1.67 ± 0.07 | 5.9 |
| end S4 | 6 | 32.39 ± 0.08 | 70.21 ± 0.03 | +2.98 | 53.17 ± 0.05 | +1.00 | 53.49 ± 0.11 | -0.29 | 69.89 ± 0.07 | -0.64 | 72.04 ± 0.17 | +3.96 | 11.57 ± 0.14 | 5.51 ± 0.14 | 2.06 ± 0.12 | 6.7 |
| end S5 | 6 | 32.52 ± 0.08 | 70.17 ± 0.05 | +2.94 | 52.72 ± 0.10 | +0.55 | 53.15 ± 0.14 | -0.62 | 70.04 ± 0.23 | -0.49 | 72.19 ± 0.22 | +4.11 | 9.33 ± 0.11 | 6.24 ± 0.13 | 1.87 ± 0.18 | 6.7 |
| end S6 | 6 | 32.04 ± 0.02 | 69.78 ± 0.04 | +2.55 | 51.64 ± 0.25 | -0.54 | 51.67 ± 0.23 | -2.10 | 70.59 ± 0.23 | +0.06 | 72.02 ± 0.30 | +3.93 | 7.98 ± 0.04 | 6.59 ± 0.17 | 2.14 ± 0.21 | 8.1 |
| end S7 | 6 | 32.97 ± 0.12 | 69.91 ± 0.06 | +2.68 | 52.18 ± 0.19 | +0.01 | 53.02 ± 0.16 | -0.75 | 71.72 ± 0.16 | +1.19 | 72.23 ± 0.18 | +4.15 | 7.10 ± 0.05 | 6.43 ± 0.12 | 2.07 ± 0.16 | 8.6 |
| end S8 | 6 | 32.15 ± 0.05 | 69.73 ± 0.06 | +2.50 | 51.39 ± 0.15 | -0.78 | 51.54 ± 0.18 | -2.23 | 70.89 ± 0.16 | +0.36 | 72.18 ± 0.16 | +4.10 | 7.94 ± 0.07 | 7.27 ± 0.12 | 1.88 ± 0.14 | 7.7 |
| end S9 | 6 | 32.29 ± 0.04 | 69.72 ± 0.07 | +2.48 | 51.32 ± 0.15 | -0.86 | 51.57 ± 0.16 | -2.20 | 71.04 ± 0.20 | +0.50 | 72.50 ± 0.10 | +4.41 | 7.71 ± 0.08 | 6.17 ± 0.14 | 1.81 ± 0.09 | 7.6 |
| end S10 | 6 | 32.05 ± 0.04 | 69.73 ± 0.04 | +2.50 | 52.00 ± 0.18 | -0.17 | 52.04 ± 0.19 | -1.73 | 70.30 ± 0.12 | -0.23 | 72.38 ± 0.27 | +4.29 | 8.02 ± 0.04 | 6.43 ± 0.14 | 1.82 ± 0.09 | 7.0 |

### C. Real-list careers: AI clubs, league mean over seeds (+/- standard error), gap to the real 2026 lists (A)
| Moment | Seeds | List size | Best 23 | Gap to A | Depth 24-38 | Gap to A | Depth 24-32 | Gap to A | U23 POT | Gap to A | Squad strength | Gap to A | U23 count | 30+ count | SD of best 23 across clubs | Best-worst club |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 start | 6 | 42.00 ± 0.00 | 67.71 ± 0.00 | +0.47 | 53.46 ± 0.00 | +1.29 | 54.86 ± 0.01 | +1.08 | 71.26 ± 0.01 | +0.72 | 68.89 ± 0.03 | +0.81 | 16.83 ± 0.00 | 6.17 ± 0.00 | 2.32 ± 0.01 | 7.8 |
| end S1 | 6 | 38.10 ± 0.04 | 69.88 ± 0.03 | +2.64 | 55.23 ± 0.02 | +3.05 | 56.66 ± 0.03 | +2.89 | 71.47 ± 0.04 | +0.93 | 70.20 ± 0.17 | +2.12 | 16.61 ± 0.07 | 4.54 ± 0.07 | 2.18 ± 0.09 | 7.7 |
| end S2 | 6 | 33.19 ± 0.05 | 70.83 ± 0.04 | +3.59 | 54.57 ± 0.04 | +2.40 | 55.17 ± 0.06 | +1.40 | 71.66 ± 0.07 | +1.13 | 72.38 ± 0.18 | +4.29 | 12.57 ± 0.07 | 5.05 ± 0.09 | 2.37 ± 0.04 | 9.2 |
| end S3 | 6 | 32.28 ± 0.05 | 70.12 ± 0.03 | +2.88 | 53.16 ± 0.12 | +0.98 | 53.32 ± 0.12 | -0.45 | 68.94 ± 0.11 | -1.59 | 72.04 ± 0.18 | +3.96 | 12.49 ± 0.10 | 5.30 ± 0.09 | 1.71 ± 0.06 | 6.5 |
| end S4 | 6 | 32.55 ± 0.10 | 70.44 ± 0.05 | +3.20 | 53.70 ± 0.07 | +1.53 | 54.16 ± 0.10 | +0.39 | 69.14 ± 0.08 | -1.39 | 72.64 ± 0.15 | +4.55 | 12.09 ± 0.08 | 4.85 ± 0.10 | 1.70 ± 0.03 | 6.8 |
| end S5 | 6 | 32.67 ± 0.05 | 70.25 ± 0.04 | +3.02 | 52.61 ± 0.16 | +0.44 | 53.12 ± 0.15 | -0.66 | 70.46 ± 0.11 | -0.07 | 72.76 ± 0.28 | +4.68 | 9.14 ± 0.05 | 5.77 ± 0.06 | 1.39 ± 0.07 | 5.3 |
| end S6 | 6 | 32.12 ± 0.04 | 69.89 ± 0.04 | +2.65 | 51.74 ± 0.07 | -0.43 | 51.85 ± 0.10 | -1.92 | 70.60 ± 0.23 | +0.07 | 72.77 ± 0.19 | +4.68 | 7.99 ± 0.05 | 6.16 ± 0.05 | 1.66 ± 0.06 | 6.8 |
| end S7 | 6 | 33.16 ± 0.06 | 70.06 ± 0.04 | +2.83 | 52.32 ± 0.12 | +0.15 | 53.30 ± 0.15 | -0.48 | 71.77 ± 0.32 | +1.23 | 72.67 ± 0.16 | +4.59 | 6.96 ± 0.07 | 5.58 ± 0.06 | 1.70 ± 0.04 | 7.4 |
| end S8 | 6 | 32.14 ± 0.06 | 69.96 ± 0.05 | +2.73 | 52.03 ± 0.13 | -0.15 | 52.16 ± 0.15 | -1.61 | 70.90 ± 0.20 | +0.37 | 72.33 ± 0.20 | +4.25 | 7.98 ± 0.05 | 6.75 ± 0.05 | 1.83 ± 0.12 | 7.4 |
| end S9 | 6 | 32.44 ± 0.15 | 69.89 ± 0.10 | +2.66 | 51.75 ± 0.13 | -0.42 | 52.16 ± 0.25 | -1.61 | 71.20 ± 0.21 | +0.67 | 72.53 ± 0.17 | +4.45 | 7.54 ± 0.08 | 5.59 ± 0.11 | 2.08 ± 0.07 | 8.2 |
| end S10 | 6 | 32.11 ± 0.04 | 69.84 ± 0.05 | +2.61 | 52.21 ± 0.19 | +0.04 | 52.31 ± 0.21 | -1.46 | 70.20 ± 0.13 | -0.34 | 72.90 ± 0.12 | +4.82 | 7.74 ± 0.11 | 6.04 ± 0.11 | 2.01 ± 0.09 | 7.6 |

### B minus C, paired by seed (redraft minus real-list career, same seed, same user club), +/- standard error
| Moment | List size | Best 23 | Depth 24-38 | Depth 24-32 | U23 POT | Squad strength | U23 count | 30+ count |
|---|---|---|---|---|---|---|---|---|
| S1 start | -2.00 ± 0.00 | -0.03 ± 0.01 | -0.82 ± 0.01 | -0.76 ± 0.02 | -0.23 ± 0.73 | -0.17 ± 0.03 | -3.50 ± 0.00 | +0.89 ± 0.00 |
| end S1 | -2.06 ± 0.10 | -0.19 ± 0.04 | -0.91 ± 0.03 | -1.15 ± 0.05 | -0.54 ± 0.71 | -0.59 ± 0.31 | -3.54 ± 0.21 | +0.89 ± 0.08 |
| end S2 | +0.31 ± 0.15 | -0.47 ± 0.04 | -0.74 ± 0.09 | -0.66 ± 0.12 | +0.71 ± 0.25 | -1.05 ± 0.16 | -1.63 ± 0.18 | +0.61 ± 0.12 |
| end S3 | -0.01 ± 0.06 | -0.25 ± 0.07 | -0.28 ± 0.19 | -0.29 ± 0.20 | +1.26 ± 0.14 | -0.89 ± 0.19 | -1.92 ± 0.19 | +0.63 ± 0.15 |
| end S4 | -0.17 ± 0.12 | -0.22 ± 0.08 | -0.53 ± 0.10 | -0.68 ± 0.13 | +0.75 ± 0.10 | -0.60 ± 0.17 | -0.52 ± 0.19 | +0.66 ± 0.22 |
| end S5 | -0.15 ± 0.10 | -0.08 ± 0.04 | +0.11 ± 0.18 | +0.03 ± 0.15 | -0.42 ± 0.19 | -0.57 ± 0.40 | +0.19 ± 0.08 | +0.46 ± 0.13 |
| end S6 | -0.09 ± 0.04 | -0.11 ± 0.07 | -0.10 ± 0.28 | -0.18 ± 0.27 | -0.01 ± 0.14 | -0.75 ± 0.38 | -0.01 ± 0.06 | +0.43 ± 0.17 |
| end S7 | -0.18 ± 0.06 | -0.15 ± 0.08 | -0.14 ± 0.28 | -0.27 ± 0.24 | -0.04 ± 0.36 | -0.44 ± 0.20 | +0.14 ± 0.10 | +0.85 ± 0.14 |
| end S8 | +0.01 ± 0.09 | -0.23 ± 0.06 | -0.63 ± 0.23 | -0.62 ± 0.28 | -0.01 ± 0.20 | -0.15 ± 0.16 | -0.04 ± 0.10 | +0.53 ± 0.16 |
| end S9 | -0.15 ± 0.12 | -0.18 ± 0.06 | -0.43 ± 0.19 | -0.59 ± 0.31 | -0.17 ± 0.08 | -0.04 ± 0.19 | +0.18 ± 0.09 | +0.58 ± 0.12 |
| end S10 | -0.06 ± 0.04 | -0.11 ± 0.04 | -0.21 ± 0.17 | -0.27 ± 0.16 | +0.11 ± 0.08 | -0.53 ± 0.23 | +0.28 ± 0.14 | +0.39 ± 0.17 |

### C. Per-club drift of AI management from the real lists (best 23, mean over non-user seeds)
| Club | A (S1 start) | S3 end | S5 end | S10 end | drift S5 | drift S10 |
|---|---|---|---|---|---|---|
| ADE | 69.3 | 72.1 | 71.3 | 69.1 | +2.0 | -0.3 |
| BRL | 67.6 | 72.8 | 71.6 | 70.2 | +4.0 | +2.6 |
| CAR | 69.0 | 69.4 | 69.5 | 70.9 | +0.5 | +1.9 |
| COL | 70.5 | 68.7 | 68.2 | 70.8 | -2.3 | +0.3 |
| ESS | 63.0 | 69.0 | 70.9 | 72.4 | +7.9 | +9.4 |
| FRE | 69.4 | 71.7 | 72.1 | 69.0 | +2.7 | -0.4 |
| GCS | 67.5 | 70.1 | 70.7 | 70.2 | +3.2 | +2.7 |
| GEE | 70.5 | 71.5 | 69.6 | 68.0 | -0.9 | -2.5 |
| GWS | 67.8 | 69.4 | 69.0 | 70.9 | +1.3 | +3.2 |
| HAW | 70.7 | 70.1 | 69.3 | 69.5 | -1.4 | -1.2 |
| MEL | 67.6 | 71.0 | 69.5 | 68.9 | +1.9 | +1.4 |
| NTH | 69.0 | 70.5 | 70.1 | 68.0 | +1.1 | -1.0 |
| PAD | 65.8 | 71.0 | 71.3 | 69.5 | +5.6 | +3.7 |
| RIC | 63.2 | 68.2 | 69.9 | 70.9 | +6.7 | +7.7 |
| STK | 66.7 | 70.5 | 71.0 | 68.2 | +4.3 | +1.5 |
| SYD | 68.8 | 70.3 | 69.7 | 68.7 | +0.9 | -0.1 |
| WBD | 67.6 | 71.7 | 70.5 | 68.8 | +3.0 | +1.2 |
| WCE | 64.7 | 67.7 | 68.8 | 69.9 | +4.1 | +5.2 |

Club order held: rank correlation of best 23 with the start, S5 -0.21, S10 -0.31. Mean absolute drift S5 2.98, S10 2.56.

### Pools the two starts draw on (mean OVR of the best 414 players, and of all)
- real seed 11: 756 players, best 414 mean 67.80, all mean 60.74
- real seed 12: 756 players, best 414 mean 67.80, all mean 60.74
- real seed 13: 756 players, best 414 mean 67.80, all mean 60.74
- real seed 14: 756 players, best 414 mean 67.80, all mean 60.74
- real seed 15: 756 players, best 414 mean 67.80, all mean 60.74
- real seed 16: 756 players, best 414 mean 67.80, all mean 60.74
- redraft seed 11: 725 players, best 414 mean 67.76, all mean 60.91
- redraft seed 12: 725 players, best 414 mean 67.76, all mean 60.91
- redraft seed 13: 725 players, best 414 mean 67.76, all mean 60.91
- redraft seed 14: 725 players, best 414 mean 67.76, all mean 60.91
- redraft seed 15: 725 players, best 414 mean 67.76, all mean 60.91
- redraft seed 16: 725 players, best 414 mean 67.76, all mean 60.91

### D1. AI picks against the best player on the board (worth = 35% OVR + 65% POT from true values, no scouting noise; League Draft: the draft's own worth)
| Draft | Pick band | Picks | Gap to best (mean) | of which scouting noise alone | noise + position need | Gap 3+ | Gap 5+ | Gap 8+ | Higher-worth players left (mean) | Pick OVR | Best OVR left | Pick POT | Best POT left |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| National, all careers | 1-10 | 1073 | 3.33 | 0.48 | 2.03 | 44% | 29% | 12% | 3.6 | 62.2 | 67.2 | 84.9 | 89.1 |
| National, all careers | 11-30 | 2159 | 5.86 | 0.66 | 1.78 | 64% | 52% | 34% | 5.4 | 55.0 | 61.7 | 76.8 | 83.8 |
| National, all careers | 31-60 | 2252 | 4.68 | 0.70 | 1.39 | 54% | 41% | 25% | 3.1 | 49.0 | 53.9 | 66.5 | 72.3 |
| National, all careers | 61-end | 2 | 0.00 | 0.00 | - | 0% | 0% | 0% | 0.0 | 48.0 | 48.0 | 68.0 | 68.0 |
| 2026 class (real-list start) | 1-10 | 56 | 1.52 | 0.65 | 1.52 | 21% | 11% | 2% | 1.9 | 66.8 | 68.6 | 88.0 | 89.8 |
| 2026 class (real-list start) | 11-30 | 124 | 2.37 | 1.03 | 1.61 | 40% | 16% | 1% | 2.7 | 61.1 | 62.8 | 77.6 | 80.5 |
| 2026 class (real-list start) | 31-60 | 114 | 1.79 | 0.98 | 1.50 | 28% | 11% | 1% | 1.9 | 54.4 | 55.6 | 65.3 | 67.5 |
| League Draft (redraft) | 1-10 | 60 | 3.33 | - | - | 32% | 18% | 8% | 20.2 | 83.0 | 91.6 | 92.4 | 96.0 |
| League Draft (redraft) | 11-30 | 120 | 3.76 | - | - | 43% | 26% | 11% | 19.1 | 79.9 | 90.6 | 90.2 | 96.0 |
| League Draft (redraft) | 31-60 | 180 | 3.77 | - | - | 39% | 28% | 14% | 19.1 | 78.4 | 89.2 | 87.5 | 94.2 |
| League Draft (redraft) | 61-end | 3960 | 3.75 | - | - | 50% | 28% | 10% | 39.8 | 59.3 | 76.7 | 67.1 | 79.5 |

### D2. Class strength by draft year (picks per career; redraft and real-list careers pooled)
| Draft year | Picks | Top 10 picks: OVR / POT | All picks: OVR / POT | Mean age |
|---|---|---|---|---|
| 2026 (real class) | 49 | 66.8 / 88.0 | 59.6 / 74.8 | 18.8 |
| 2027 | 49 | 66.5 / 89.6 | 57.2 / 77.7 | 19.7 |
| 2028 | 48 | 58.1 / 83.5 | 50.1 / 72.7 | 19.6 |
| 2029 | 49 | 61.1 / 83.3 | 53.2 / 73.8 | 19.6 |
| 2030 | 47 | 62.1 / 86.1 | 55.2 / 75.4 | 19.8 |
| 2031 | 52 | 61.7 / 82.9 | 53.9 / 73.5 | 19.4 |
| 2032 | 50 | 61.2 / 84.1 | 54.1 / 74.8 | 19.5 |
| 2033 | 53 | 62.6 / 84.8 | 53.9 / 73.3 | 19.6 |
| 2034 | 55 | 63.6 / 84.2 | 54.0 / 73.5 | 19.6 |
| 2035 | 55 | 63.0 / 86.0 | 53.7 / 73.1 | 19.6 |

### D3. Drafted players three seasons on, against the real 2026 lists' players of the same age
| Age three seasons on | Drafted | Still on a list | OVR of those still listed | Real 2026 lists, same age: players | Real OVR | Gap |
|---|---|---|---|---|---|---|
| 20 | 46 | 100% | 68.3 | 79 | 53.5 | +14.8 |
| 21 | 237 | 100% | 67.5 | 73 | 56.3 | +11.3 |
| 22 | 1998 | 100% | 68.6 | 46 | 57.7 | +10.8 |
| 23 | 1768 | 96% | 67.8 | 68 | 59.9 | +7.9 |
| 24 | 376 | 79% | 69.3 | 59 | 60.6 | +8.8 |
| 25 | 42 | 88% | 60.7 | 41 | 63.6 | -2.9 |

Same cohort by class (three seasons on, those still listed):
| Class | Drafted | OVR at the pick | Age at the pick | OVR three seasons on | Age then | Rise |
|---|---|---|---|---|---|---|
| 2026 (the real class) | 283 | 59.9 | 18.8 | 67.7 | 20.8 | +7.8 |
| 2027 (first generated) | 502 | 58.4 | 19.7 | 68.8 | 22.7 | +10.4 |
| 2028 and later (generated) | 3524 | 53.6 | 19.6 | 68.2 | 22.6 | +14.6 |

Same cohort by pick band (three seasons on; OVR/POT at the pick are for those still listed):
| Pick band | Drafted | Still listed | OVR at the pick | OVR three seasons on | POT at the pick | Rise |
|---|---|---|---|---|---|---|
| 1-10 | 890 | 100% | 62.2 | 77.5 | 85.1 | +15.3 |
| 11-30 | 1804 | 100% | 55.4 | 69.6 | 76.8 | +14.2 |
| 31-60 | 1772 | 91% | 49.4 | 61.5 | 67.0 | +12.2 |
| 61-end | 2 | 100% | 48.0 | 65.0 | 68.0 | +17.0 |

Real 2026 lists by age (players, OVR, POT): 18: 6, 57.2, 69.5; 19: 50, 54.4, 73.9; 20: 79, 53.5, 69.3; 21: 73, 56.3, 71.2; 22: 46, 57.7, 67.9; 23: 68, 59.9, 69.8; 24: 59, 60.6, 67.4; 25: 41, 63.6, 70.8; 26: 285, 65.6, 67.2

## Runs

audit.yml on CI, tool `draft_strategy_impl`, 10 seasons, seeds/user clubs 11 MEL, 12 COL, 13 ADE, 14 CAR, 15 GEE,
16 SYD, commit 183079b0 (branch claude/ai-draft-audit).

- Base (`redraft`, `real`): runs 41486993353, 41486998596, 41487004011, 41487009909, 41487016004, 41487022056,
  41487029685, 41487038199, 41487047432, 41487053634, 41487062215, 41487071601.
- Buff (`redraft_buff`, `real_buff`): runs 41487668856, 41487675264, 41487683235, 41487690287, 41487696389,
  41487703528, 41487711487, 41487718105, 41487725298, 41487733321, 41487742809, 41487749157.

Paired table: each seed's AI-club league mean, buff minus base, mean ± standard error over the 6 seeds; the pick gap
is each seed's mean (best worth left minus the pick's worth) over National Draft picks in the band.
