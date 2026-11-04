# Believable comebacks: sim vs real AFL (TODO row 42), 2026-11-05

**Result: comeback rates already match real AFL. No rule change is made.** Of 26 comeback
measures, 24 sit inside two standard errors of real AFL in AI-vs-AI play (2 NEAR) and 25 in
coach-vs-AI play (1 NEAR); none is OUT. A 50-point last-quarter swing happens in 0.5% of sim matches against
0.8% real, so the 52-point swing the director saw (2026-10-13) is "very very very unlikely", as
he asked. Balance stays his call.

## Method

- **Real AFL:** every match on AFL Tables, 2010-2025 (3,261 matches, finals included), with
  cumulative points at quarter time, half time, three-quarter time and the end of Q4 (extra time
  not counted). Stored in `tools/balance/afl_comebacks.json`.
- **Sim:** `tools/audit/comeback_impl.gd` on current main (62f6a717), 4,800 matches per mode on
  GitHub runners via audit.yml (8 batches of 600, seeds 11-18 and 21-28), random club pairs,
  weather drawn 4 perfect : 1 wet : 1 windy : 1 hot.
  - `ai`: both clubs coached by the AI (the league's matches).
  - `coach`: side 0 keeps one call all game (balanced, steady) like a coach who skips Q4; the AI
    club chases or protects as usual. This is the situation of the director's 52-point swing.
- **Report:** `python tools/balance/comeback_report.py <logs>`. IN = within 2 standard errors of
  real; NEAR = within 3 SE + 3 points; OUT beyond.

Leader rows: how often the side in front at that break won (draws count half). Swing rows: share
of matches whose last-quarter margin change was at least that many points.

## AI v AI (4,800 matches)

| Moment | Real AFL | base (n) | base vs real |
|---|---|---|---|
| QT 1-6 |  54.4% (908) |  55.9% (1312) | IN |
| QT 7-12 |  65.7% (774) |  67.0% (1090) | IN |
| QT 13-18 |  72.3% (562) |  73.8% (902) | IN |
| QT 19-24 |  81.7% (421) |  79.9% (602) | IN |
| QT 25-30 |  83.5% (233) |  88.1% (375) | IN |
| QT 31-36 |  89.0% (164) |  95.0% (220) | NEAR |
| QT 37-999 |  99.1% (109) |  96.4% (181) | IN |
| HT 1-6 |  61.1% (619) |  59.4% (812) | IN |
| HT 7-12 |  66.1% (598) |  68.1% (821) | IN |
| HT 13-18 |  77.8% (457) |  78.8% (713) | IN |
| HT 19-24 |  84.9% (428) |  85.8% (622) | IN |
| HT 25-30 |  91.6% (334) |  91.0% (525) | IN |
| HT 31-36 |  93.5% (261) |  95.5% (423) | IN |
| HT 37-999 |  98.7% (513) |  98.5% (813) | IN |
| 3QT 1-6 |  57.5% (449) |  65.8% (644) | NEAR |
| 3QT 7-12 |  73.2% (478) |  76.6% (618) | IN |
| 3QT 13-18 |  83.1% (413) |  84.9% (589) | IN |
| 3QT 19-24 |  93.5% (367) |  93.4% (544) | IN |
| 3QT 25-30 |  95.1% (315) |  96.3% (503) | IN |
| 3QT 31-36 |  98.2% (271) |  98.7% (398) | IN |
| 3QT 37-999 |  99.8% (928) |  99.9% (1456) | IN |
| Q4 swing >=20 |  27.1% (3261) |  25.5% (4800) | IN |
| Q4 swing >=30 |   9.8% (3261) |   8.9% (4800) | IN |
| Q4 swing >=40 |   2.9% (3261) |   2.5% (4800) | IN |
| Q4 swing >=50 |   0.8% (3261) |   0.5% (4800) | IN |
| won from 24+ down at 3QT |   0.7% (3261) |   0.6% (4800) | IN |



## Coach v AI (4,800 matches)

| Moment | Real AFL | base (n) | base vs real |
|---|---|---|---|
| QT 1-6 |  54.4% (908) |  55.6% (1336) | IN |
| QT 7-12 |  65.7% (774) |  69.9% (1177) | IN |
| QT 13-18 |  72.3% (562) |  75.3% (873) | IN |
| QT 19-24 |  81.7% (421) |  82.5% (595) | IN |
| QT 25-30 |  83.5% (233) |  87.1% (349) | IN |
| QT 31-36 |  89.0% (164) |  91.4% (191) | IN |
| QT 37-999 |  99.1% (109) |  97.7% (155) | IN |
| HT 1-6 |  61.1% (619) |  58.2% (880) | IN |
| HT 7-12 |  66.1% (598) |  72.5% (850) | NEAR |
| HT 13-18 |  77.8% (457) |  79.0% (782) | IN |
| HT 19-24 |  84.9% (428) |  86.6% (598) | IN |
| HT 25-30 |  91.6% (334) |  91.5% (514) | IN |
| HT 31-36 |  93.5% (261) |  96.0% (340) | IN |
| HT 37-999 |  98.7% (513) |  99.0% (770) | IN |
| 3QT 1-6 |  57.5% (449) |  61.5% (648) | IN |
| 3QT 7-12 |  73.2% (478) |  76.9% (670) | IN |
| 3QT 13-18 |  83.1% (413) |  82.9% (609) | IN |
| 3QT 19-24 |  93.5% (367) |  93.4% (520) | IN |
| 3QT 25-30 |  95.1% (315) |  96.7% (488) | IN |
| 3QT 31-36 |  98.2% (271) |  98.5% (392) | IN |
| 3QT 37-999 |  99.8% (928) |  99.9% (1426) | IN |
| Q4 swing >=20 |  27.1% (3261) |  26.2% (4800) | IN |
| Q4 swing >=30 |   9.8% (3261) |   9.7% (4800) | IN |
| Q4 swing >=40 |   2.9% (3261) |   2.6% (4800) | IN |
| Q4 swing >=50 |   0.8% (3261) |   0.5% (4800) | IN |
| won from 24+ down at 3QT |   0.7% (3261) |   0.6% (4800) | IN |



Who comes back in coach mode, from 19+ points down at three-quarter time: the coach's side won
28 of 1,340 (2.1%), the AI club 26 of 1,486 (1.7%). The AI chasing late does not manufacture
comebacks.

## What it means

- The levers that drive late swings (momentum at `MOMENTUM_EDGE` 0.04, Q4 fatigue, the AI's
  chase and protect calls) together produce real AFL comeback rates. Tuning any of them now
  would move the sim away from real AFL, so this PR changes no rule.
- The NEAR bands are small: QT 31-36 (95.0% v 89.0%) and HT 7-12 in coach mode. The one that
  matters is AI v AI, 1-6 points up at three-quarter time: the leader wins 65.8%
  against 57.5% real, so tight finishes are slightly more predictable than real AFL. Coach mode
  has it IN (61.5%). A fix would make close games more random, not comebacks bigger; it is
  left for his call.
- The director's 52-point swing predates later engine work (match flow, fatigue and the
  momentum edge settled since 2026-10-13); at today's rates a 50+ point Q4 swing comes once in
  about 200 matches, roughly one every year of a 23-round season for some club in the league,
  and rarer for your club.

## Not exercised

- A human coach who actively chases or shuts down a game (both modes use fixed or AI calls).
- Moments and in-match decision cards (off in the audit: skip takes the default).
- Finals pressure and extra time; real data includes finals, the sim pairs are home-and-away.
- Rain, wind and heat at full effect (row 61 is not built).

## Rerun

```bash
gh workflow run audit.yml --ref <branch> -f impl=comeback_impl -f args="ai 11 600 base"
gh run download <id> -n audit-comeback_impl -D run_<id>
python tools/balance/comeback_report.py run_*/*
```
