# 2026 National Draft: the real picks (1.1 patch)

Checked 2026-11-21, the day after the draft (night one 19 November, night two 20 November 2026, Marvel Stadium). This follows [TRADE_PERIOD_2026_LIST_CHANGES.md](TRADE_PERIOD_2026_LIST_CHANGES.md). The rookie draft (23 November 2026) and the pre-season supplemental period had not happened when this was built; neither is in the data. TODO row 113 ("Each club's real 2026 National Draft picks", parked until the draft happened) is what this delivers.

## The person's ruling (2026-11-21)

Asked whether a real-lists career starts before or after the real draft, the person chose **"Both, chosen at New career"**:

- **Before the draft** (as before): the end-of-2026 lists after the trade period, and you run your club through the 2026 National Draft. The pool now holds every man really drafted.
- **After the draft**: all 65 men taken on 19 and 20 November start on the club that took them, with their real pick, round and a rookie deal. The opening draft is left with the prospects nobody took, so your Forge prospect and the Forge club's new-club picks still have a draft to enter (director 2026-11-15: every mode hosts the Forge).

## Counts

| | Count |
|---|---:|
| Selections | 65 (19 in round one, then 24, 15 and 7) |
| Father-son, NGA and academy bids matched | 9 (Cochrane, Walker, Matthews, el Souki, McCartney, Justice, Hodge, Boi, McGroder) |
| Tied players whose club did not match | 3 (Murray to Sydney, Long to Geelong, Medved to Fremantle) |
| Delisted players redrafted | 3 (Knevitt to Sydney; Himmelberg and Ugle-Hagan back to Gold Coast) |
| Already in the game's class (Rookie Me's ranking) | 41 |
| Added to the class (not in the ranking) | 21 |
| Passes | 9 at the end of night two |

## What the game does with this

- `data/national_draft_2026.csv` (new): one row per pick: pick, round, name, birth date, club, height, position, the team and league he came from, `kind` (`national`, `FS`, `NGA`, `academy`, `redrafted`), the club that bid, the clubs the pick came through (`via`), compensation notes, sources. `GameDB.national_draft` loads it; `GameDB.national_pick(p)` finds a player's row by name and birth date, or by surname and birth date, or by full name (the class has "Lochie" Burrows; the sources disagree on Archie Spencer's birth date, see below).
- `data/draftees_2026.csv`: 21 rows added (ranks 57-77, `data_src` `afl-draft-nov26`) for the men drafted who were not in the Rookie Me ranking the class was built from. They have no U18 numbers, so they are rated from the pick they went at (`draft_rank` = real pick, the public verdict on them), and their profile does not call them "Ranked". McCartney and Hodge (father-son) and Boi (Hawthorn NGA) carry their ties; Long (Adelaide NGA) and Medved and McGroder (Sydney academy) do not, as the existing class does not tie the northern academies and Adelaide passed on Long. The 41 existing rows are unchanged.
- `GameState.real_after_draft` and New career's "2026 draft" row (today's real lists only): `begin_real_lists` places each pick (`_place_real_draft`) after the trade-period moves and the tied prospects. A prospect leaves the pool; Knevitt and Ugle-Hagan leave the delisted free agents; Himmelberg is already on Gold Coast's list (`list_additions_2026.csv`). Saved with the career.
- `departures_2026.csv` keeps Knevitt and Ugle-Hagan as delisted: true before the draft. The after-the-draft start takes them off the free agents.
- Guernsey numbers: none are announced yet; each draftee gets a free number on his list (`_next_jumper_number`), as the opening draft gives.
- Looks: draftees have no row in `player_appearance.csv` (no club photos yet), so they show the uncurated look, as the class always has. Knevitt and Ugle-Hagan keep theirs.
- Draft-pick trades on the night (at least eight swaps) and the traded future picks are not in the game's pick model; the opening draft order is unchanged (reversed 2026 ladder).

## Sources

- Every pick, club and recruiting team: [Wikipedia, 2026 AFL draft](https://en.wikipedia.org/wiki/2026_AFL_draft) (raw wikitext, fetched 2026-11-21) and [SEN's pick-by-pick](https://www.sen.com.au/news/2026/11/15/afl-national-draft-2026-draft-order-top-prospects-every-selection-pick-by-pick). They agree pick for pick on all 65. Wikipedia's table numbers Harper Banfield's pick 74; SEN, Zero Hanger and Draftguru say 65 (the last pick), and 65 is used.
- Birth date and height: each player's [Draftguru](https://www.draftguru.com.au/years/2026) page.
- Position and home state for picks 20-65: [Zero Hanger's night-two tracker](https://www.zerohanger.com/afl-draft-live-every-pick-best-available-prospects-draft-order-and-trade-deals-for-night-two-187462/); picks 1-19 keep the class file's position. Three disagree with SEN's call on the night: Jackson Watkins (SEN general forward, Zero Hanger midfielder), Ben Forster (SEN midfielder, Zero Hanger defender), Jack Riding (SEN general forward, Zero Hanger midfielder). SEN's is used. Kaie Sullivan (midfielder) and Zach Stevens (general forward) are SEN's only. Home state: Stevens (South Barwon) and Riding (North Ballarat) are Victoria Country from their Draftguru origins; Zero Hanger lists Riding as South Australia.

## Disagreements left as they are

- Archie Spencer's birth date: the class file (Rookie Me) has 2008-03-24, Draftguru 2008-09-24. The class row is unchanged; the draft row has Draftguru's.
- Heights: Draftguru's post-combine heights differ from the class file by 1-4 cm for 22 players (Caylen Murray 183 vs 179). The class rows are unchanged; the draft rows have Draftguru's.
- Wikipedia's infobox gives the rookie draft as 23 November; its key-dates table agrees. Not yet held.

## Per club

| Club | Picks | Players (pick) |
|---|---:|---|
| Adelaide | 3 | Toby Krasna (14), Xavier Ladbrook (34), Sam Tassone (44) |
| Brisbane Lions | 4 | Kodah Edwards (27), Archie Van Dyk (28), Jackson Phillips (29), Archie Spencer (36) |
| Carlton | 4 | Cody Walker (3), Harvey Spawton-Guy (32), Jackson Watkins (37), Ethan Herbert (46) |
| Collingwood | 4 | Sam Gayfer (12), Gus Kennedy (31), Jordan Knapp (41), Koby LeCras (62) |
| Essendon | 5 | Ethan Drever (2), Archie Elliott (17), Harvie Cooke (21), Jack Pickett (26), Blake Justice (55) |
| Fremantle | 3 | George Dimer (18), Kane Johnston (42), Jake Medved (57) |
| GWS Giants | 3 | Ethan Matthews (6), Jake Eime (13), Andrio Sousa (45) |
| Geelong | 3 | Lachlan Hicks (38), Anthony Long (56), Zach Stevens (60) |
| Gold Coast | 3 | Leo Steed (10), Elliot Himmelberg (63), Jamarra Ugle-Hagan (64) |
| Hawthorn | 3 | Benji van Rooyen (30), Cooper Hodge (58), Keenan Boi (59) |
| Melbourne | 4 | Mitch Harris (7), Lachlan Burrows (15), Ben Forster (49), Kaie Sullivan (52) |
| North Melbourne | 3 | George Gale (23), Seb Marsic (35), Aidan McCartney (54) |
| Port Adelaide | 6 | Dougie Cochrane (1), Clancy Snell (19), Wil Malady (20), Wil Antrobus (25), Gabe Patterson (39), Angus White (47) |
| Richmond | 4 | Arki Butler (4), Harry Van Hattum (8), Noah Williams (22), Harry Franz (51) |
| St Kilda | 3 | Gus Teixeira (11), Tyson Bradley (16), Lewis Houndsome (43) |
| Sydney | 4 | Caylen Murray (9), Brady Wright (40), Mitch Knevitt (48), Mason McGroder (61) |
| West Coast | 3 | Heath Mellody (5), Jake Soutar (24), Harper Banfield (65) |
| Western Bulldogs | 3 | Khaled el Souki (33), Jack Riding (50), Sam Devers (53) |
