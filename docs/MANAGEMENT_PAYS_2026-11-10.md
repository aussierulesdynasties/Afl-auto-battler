# Management pays: 10-season audit (TODO row 67, 4.Q11)

`tools/audit/levers2_impl.gd`, run on GitHub (`audit.yml`), 20 League Draft careers per arm
(seeds 301-320, paired), 10 seasons each, your club on autopilot at matches. Measurement only:
no rule changed.

| Arm | What the coach does | Seasons | Flags | Grand finals | Top 4 | Mean ladder (±SE) | Trades | Projects |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Lists only (baseline) | 190 | 12 | 29 | 59 | 9.25 ± 0.53 | 0 | 0 |
| B | Works the trade period | 190 | 16 | 27 | 59 | 9.21 ± 0.53 | 13 | 0 |
| C | Elite recruiting, paid (Development Minimal) | 200 | 25 | 37 | 58 | 9.18 ± 0.50 | 0 | 0 |
| D | Both development-project places busy | 197 | 23 | 36 | 64 | 8.97 ± 0.50 | 0 | 126 |
| E | All three | 200 | 23 | 36 | 74 | 8.62 ± 0.48 | 7 | 123 |

Flags per season: A 6.3%, B 8.4%, C 12.5%, D 11.7%, E 11.5% (an even share is 5.6%).

## What it says
- **The recruiters' edge already exists.** Rivals draft on the shared noisy read
  (`DraftScouting.projection`, Standard width); your Recruiting budget narrows only yours
  (Elite 0.65x). No new mechanic was built. Paid for with Development, it roughly doubles
  flags against the baseline, without moving the mean ladder much.
- **Development projects** help about as much, and lift top-four finishes.
- **All three** gives the best ladder and the most top-four finishes (74 of 200), but no more flags
  than C or D alone.
- **The trade period is not at real volume for the coach.** The audit's trading coach landed
  13 trades in about 180 off-seasons (0.07 a year) against about 1.4 per club in real AFL. League
  volume (#383) is rival-to-rival; a coach asking for an upgrade with spare assets rarely gets one.
- 20 careers per arm is small: flag counts carry a standard error of about ±4. Some A, B and D
  careers stopped early when an off-season did not complete (190-197 seasons, not 200).

Balance is the director's call.
