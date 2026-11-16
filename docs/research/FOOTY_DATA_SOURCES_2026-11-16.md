# Footy data sources for the football proof (row 201)

_2026-11-16. Two sources the director pointed at: dfsaustralia.com ("theres HEAPS of resources on that site
that oculd be useful for our sim ... its paywalled / gather what you can from the free samples") and
github.com/AFLgains/AIFL. Only what the site shows free, through normal page use, was read. Nothing was
downloaded and no paywalled page was opened another way._

## DFS Australia: what is free

Champion Data numbers, displayed per team and season. Team and season are page addresses, e.g.
`/afl-cbas/?team=CAR&season=2026`.

| Page | Free? | What it holds | Seasons | Use for the sim |
|---|---|---|---|---|
| Player Maps (`/player-maps/`) | yes | every player's disposals, marks and scoring shots per match as x,y points in metres from the centre (axes ±83 m), with kick, handball, mark, goal, behind, missed shot told apart | 2023-2026, every listed player (953) | where each kind of player wins and uses the ball: the event geography for row 201's spec (a key back's kicks from the back 50, a wing's along the boundary, a small forward's marks inside 50) |
| Centre Bounce Attendances (`/afl-cbas/`) | yes | each player's share of centre bounces attended, per round and for the season | every team and season tried (Adelaide, Carlton 2026) | who stands at a centre bounce and how midfields rotate: McAndrew 77%, Berry 70%, Dawson 68% (Adelaide 2026); Cripps 80%, Pittonet 76%, Walsh 73% (Carlton 2026) |
| Kick-In Breakdown (`/afl-kickins/`) | yes | kick-ins taken and played on, per player per round | 2021-2026 | who kicks in and how often he plays on: Milera 79 kick-ins, all played on; Worrell 75, 92% (Adelaide 2026). The kick-in phase's shape |
| Ruck Contests (`/afl-ruck-contests/`) | yes | ruck contests attended per round and hitout share | 2013-2026 | ruck share and the second ruck: McAndrew 45% of hitouts at ~70-80% of contests (Adelaide 2026); Gawn 54% at ~80-90% (Melbourne 2016) |
| Team Score Sources (`/team-score-source/`) | yes | fantasy points by chain origin (centre bounce, ball-up, throw-in, turnover, kick-in) per match, team and player | 2024-2026 | how play starts: chains that start from a turnover earn most of a side's fantasy points (Adelaide round 1 2026: 1,114 of 1,673), stoppages most of the rest. Fantasy points, not scores |
| Midfields (`/afl-midfields/`) | **paywalled** | centre-bounce trios by game | | |
| DVP Player Positions (`/dvp-player-positions/`) | **paywalled** | positions clustered from the last ten games | | |

Not yet looked at: Fantasy Score Sources and the site's other pages; the season packs' downloads.

### What it gives row 201

- **Where the ball is used, by position.** Player maps are the one free source of real event positions.
  Grouping players by role (Wheelo positions are already in `docs/research/wheelo/`) gives, for each role, where
  he kicks, handballs and marks. The harness can mark our MatchSim events IN, NEAR or OUT against that.
- **Stoppage set-ups.** Attendances say which men stand at a centre bounce and a ruck contest, and how often.
- **Kick-ins.** One or two kick-in specialists per side, and how often they play on.
- **How play starts.** Score sources split chains by origin (stoppage against turnover): a check on our sim's mix.
- **Not in it:** where the 36 men stand off the ball. No free page has team shape, length, width or men behind
  the ball; those still come from footage and published tracking studies.

## AFLgains/AIFL (MIT licence)

An Australian Rules engine for writing bots: 8 a side on a 140 × 100 m oval (the main game) and 18 a side on
160 × 130 m. Bots give each player an order about once a second; a four-minute game plays in about a second.

- **Not a source of real numbers.** Its player attributes are set by hand (e.g. `ruck: marking_skill 0.94`
  in `src/aflsim/games/afl18/config.py`) and nothing is fitted to AFL data. The 18-a-side game reuses the
  8-a-side laws and bots. It cannot stand as evidence in row 201's spec.
- **Worth reading as design ideas for row 201's shape models:**
  - `controllers/rules_zoo.py`: scripted teams, one idea each (ZoneBot "a rolling zone without the ball",
    PressBot, StackBot, WallBot covering the defensive 62 m, LeadBot leading into 9 m of space). The same
    calls our coach makes, written as per-player rules.
  - `physics.py`: kick error that grows with distance, pressure and running speed, and a pressure field
    summed from opponents' distances.
- Its blog ("Claude Code can be a football analyst") rates positions with a network trained on its own games.
  That is a method idea only; the data are bot games.

The MIT licence allows reuse with its notice kept, but nothing here is worth copying into the game: our sim
and MatchDirector already own these jobs.
