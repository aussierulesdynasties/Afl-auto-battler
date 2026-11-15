# The 2016 supplements bans (TODO row 142, L10)

Researched 2026-11-13 for the Supplements saga switch (director, 2026-11-13: "maybe put the drugs saga as its own
toggle in game creation as its punishment (full 1 year ban of list) is far more severe"). Public record only.

## What happened

- 12 January 2016: the Court of Arbitration for Sport upheld the World Anti-Doping Agency's appeal and found 34 past
  and present Essendon players guilty over the club's 2012 supplements program. Each got a two-year ban, backdated,
  so the players still on AFL lists missed the whole 2016 season, finals included, and were free to play in 2017.
- 17 of the 34 were retired or delisted by then; 17 were on AFL lists: 12 at Essendon, 5 at other clubs.
- The AFL let Essendon sign up to ten top-up players on one-year deals for 2016 (James Kelly, Ryan Crowley, Mark
  Jamar, Matt Dea, Sam Michael and others). The 2013 penalties (a $2m fine, the finals ban, lost 2013 and 2014 first
  and second-round picks) are the existing `supplements_saga` event.

## The players banned for 2016, by their 2016 club

Each is checked against `data/legacy/2010s/lists.csv` (year 2016): club, name and date of birth match. The game
finds them by surname and date of birth.

| Player | Date of birth | 2016 club |
| --- | --- | --- |
| Jobe Watson | 1985-02-08 | Essendon |
| Brent Stanton | 1986-05-01 | Essendon |
| Cale Hooker | 1988-10-13 | Essendon |
| David Myers | 1989-06-30 | Essendon |
| Michael Hurley | 1990-06-01 | Essendon |
| Michael Hibberd | 1990-01-03 | Essendon |
| Tayte Pears | 1990-03-24 | Essendon |
| Tom Bellchambers | 1989-07-09 | Essendon |
| Travis Colyer | 1991-08-24 | Essendon |
| Dyson Heppell | 1992-05-14 | Essendon |
| Ben Howlett | 1988-10-21 | Essendon |
| Heath Hocking | 1987-12-27 | Essendon |
| Jake Carlisle | 1991-10-01 | St Kilda |
| Angus Monfries | 1987-01-19 | Port Adelaide |
| Paddy Ryder | 1988-03-14 | Port Adelaide |
| Stewart Crameri | 1988-08-10 | Western Bulldogs |
| Jake Melksham | 1991-08-29 | Melbourne |

## How the game applies it (saves make their own history)

- The event `supplements_bans` fires in the first week of 2016, before round 1, when the career has the Supplements
  saga switch on.
- Who is banned: when the saga broke in this career (2013), the game noted Essendon's list. In 2016 a named player is
  banned only if he was on it, wherever he plays now (a player the save traded away is still banned). A save where he
  never played at Essendon does not ban him. A career that began after 2013 bans every named player still listed.
- A banned player cannot be picked for any 2016 match, finals included; the ban lifts in the first week of 2017.
- Top-up rule, the simplest form: Essendon sign one player for each of their own banned players, up to ten, the
  best-rated left in the mid-season draft's pool (unsigned free agents, passed-over prospects), on the senior minimum
  for 2016 only. The news names them.
- Known limit: only the 17 still listed in real 2016 are named. A save that kept one of the other 17 on a list would
  not ban him.

## Sources

- AFL.com.au, "Guilty: Court bans the Essendon 34 for 2016", 12 Jan 2016:
  https://www.afl.com.au/news/52804/guilty-court-bans-the-essendon-34-for-2016
- SBS News, "17 current AFL players banned for doping", 12 Jan 2016:
  https://www.sbs.com.au/news/article/17-current-afl-players-banned-for-doping/3r2kpxwcf
- InDaily, "Port 'devastated' for suspended stars as Bombers banned", 12 Jan 2016:
  https://develop.indailysa.com.au/news/archive/2016/01/12/bombers-guilty-several-players-to-miss-season
- Al Jazeera, "Australian football team floored by mass doping bans", 12 Jan 2016:
  https://www.aljazeera.com/sports/2016/1/12/australian-football-team-floored-by-mass-doping-bans
- AFL Players' Association, "Everything you need to know about Essendon's 10 top-up players":
  https://www.aflplayers.com.au/news-feed/stories/everything-you-need-to-know-about-essendons-10-top-up-players
- AFL.com.au, "Essendon's available list for 2016", 1 Mar 2016:
  https://www.afl.com.au/news/2016-03-01/essendons-available-list-for-2016
- Club, name and date of birth: `data/legacy/2010s/lists.csv` (DraftGuru and AFL Tables, checked 2026-11-10).
