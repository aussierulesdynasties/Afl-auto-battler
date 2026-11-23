# A Forge club's first seasons on real lists (2026-11-23)

Bug bash: the director's AI-run Forge club, Coburg, was the highest-rated side
in the league in a real-lists (not redraft) career.

## Cause

A new club's 30 state-league signings (`Expansion.foundation_list`) were made by
`Prospects.generate_expansion_list` ranked 1 to 30, which `Prospects.project`
rates as picks 1 to 30 of a draft class (`RANK_BANDS`: 70 down to 58) with no
draft-night discount (`DRAFT_NIGHT_SCALE` only touches draft classes). The best
came in at 70-74, a club's fifth-best player; 17-year-olds at 67. Against the
real 2026 lists (a club's 5th-best averages 73, its 22nd 58) that is a near
average best 22 on day one, before its seven first-round picks and free agents.

## Fix

With the expansion concessions (Forge clubs, Tasmania, Canberra) the signings
are ranked from `Prospects.DEPTH_FIRST_RANK` (40), the rule already used for the
state-leaguers who fill out a League redraft: about 45-62, a list's depth. A club
entering before the concessions (Adelaide 1991 and the like, building its whole
list from its state league's best) is unchanged.

## Method

`tools/audit/forge_start_impl.gd`: real 2026 lists, a Forge club (Coburg),
you coach Richmond or Geelong, every draft and off-season run by the rival AI.
Paired seeds, main (before) against the branch (after): 12 careers x 6 seasons
on GitHub (`audit.yml`, seeds 401-412) and 4 careers x 5 seasons locally
(301-304). Strength = average of the best 22 by rating; Rating rank = the
ladder's Rating column (`GameState.club_strength`).

## Results (means over 16 careers; year 6 over 12)

| Club year | Before: ladder | wins | strength rank | After: ladder | wins | strength rank |
|---|---|---|---|---|---|---|
| Entry | | | 13.2 of 19 (best 22 -0.8 vs league) | | | 19.0 of 19 (-11.3) |
| 1 | 14.9 | 6.4 | 11.5 | 17.9 | 3.8 | 19.0 |
| 2 | 14.4 | 7.6 | 8.9 | 19.1 | 3.0 | 19.4 |
| 3 | 14.1 | 8.6 | 6.6 | 18.2 | 4.6 | 18.9 |
| 4 | 10.7 | 11.2 | 3.8 | 16.8 | 5.9 | 17.6 |
| 5 | 10.8 | 11.1 | 3.1 | 15.1 | 7.8 | 13.7 |
| 6 | 9.7 | 11.9 | 4.0 | 13.0 | 9.2 | 6.2 |

Before, the list was the league's 3rd-4th best by year 4 (1st in some careers):
the "highest rated" the director saw. After, it is bottom-four in 15 of 16
first seasons and climbs to the top six lists by year 6.

Real reference (wins, ladder): Gold Coast 2011-16: 3 (17th of 17), 3 (17th),
8 (14th), 10 (12th), 4 (16th), 6 (15th). GWS 2012-17: 2 (18th), 1 (18th), 6
(16th), 11 (11th), 16 (4th), 14 (4th). The new curve sits between them: as weak
early, a little slower than both in years 3-4 (about 5 wins against their 7-10).

Tasmania (enters 2028 on the same signings plus its rival approaches and traded
picks), club years 1-5, ladder before 15.8 / 13.6 / 12.8 / 10.9 / 12.8, after
17.4 / 17.9 / 17.2 / 16.2 / 15.2.

## Not exercised

- A Forge club you coach yourself (the audit leaves it to the AI).
- League redraft and Legacy starts (the Forge club there drafts its list, or
  takes real foundations; the change only reaches generated state-leaguers).
- Balance is the director's call: these numbers are the agent's screen only.
