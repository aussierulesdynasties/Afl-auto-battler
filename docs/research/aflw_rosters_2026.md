# AFLW rosters, 2026

Research only. Nothing here decides whether AFLW goes in the game, and nothing is imported.
The data is in [aflw_rosters_2026.csv](aflw_rosters_2026.csv).

**As of 9 November 2026.** The 2026 season is still running (9 August to 27 November; the first week of finals has been played), so games and goals are not final.

**Result:** 585 players across all 18 clubs. 16 clubs come to exactly 30 active players, the size the rules set. Collingwood and Gold Coast each come to 32 and I could not settle why (see "Not settled").

## How to read the CSV

A main column (`dob`, `height_cm`, `gm`, `gl`, `draft_year`, `draft_pick`, `draft_type`) is filled only when no source contradicts it. If sources disagree it is blank, and each source's own value stays in the columns named after it (`dob_afl`, `dob_footyinfo`, `dob_wikipedia` and so on). I did not choose a winner, even where two sources outvote one.

Column names follow the men's data where the meaning is the same: `club,num,last,first,dob,age,height_cm,gm,gl,draft_year,draft_type,draft_pick,list,position`.

- `position` is the AFL feed's word, unchanged. It has one source only.
- `age` is Footyinfo's figure in whole years.
- `gm`, `gl` are career totals; `gm_2026`, `gl_2026` are this season, both from Footyinfo.
- `draft_type` is national, pre-season or rookie, read from Footyinfo's pick label. Blank means no draft pick is recorded.
- `how_joined_club` is the section of Wikipedia's draft or player movement page holding that player's latest entry for this club. Blank means I found no entry; it does not mean anything about the player.
- `list` is senior or rookie, from Wikipedia. Wikipedia's rookie marks may be incomplete: some clubs' templates have the rookie key commented out, so a senior there is not proof.
- `list_status` is active, inactive, or a top-up or replacement label.
- `left_after_2026`: the list is the 2026 one, so players who have since gone stay in it. Only retirements I saw confirmed say "retired".

## List size

The AFLW Competition Rules (effective 11 June 2025), rule 3.1, set a list of 30: 27 to 30 primary players and up to 3 rookies. Rule 7 covers inactive players and replacements, and they sit on top of the 30. AFL reporting confirms "30 active players" this season, and allows top-ups from state leagues when a club falls under 24 available.
[Rules PDF](https://resources.afl.com.au/afl/document/2025/08/21/549bb3bb-0466-4b69-982e-38d4f03ca3aa/AFLW-Competition-Rules-effective-11-June-2025-1.pdf).

## Count per club

Active here includes confirmed replacements only where the row says so; "Top-up or replacement" is counted separately. Expected: 30 active, plus inactive and any top-ups.

| Club | In CSV | Active | Inactive | Top-up or replacement | Rookies marked | Against 30 |
| --- | --: | --: | --: | --: | --: | --- |
| ADE | 33 | 30 | 3 | 0 | 3 | Matches |
| BRL | 32 | 30 | 2 | 0 | 2 | Matches |
| CAR | 32 | 29 | 2 | 1 | 2 | Matches once the replacement fills the inactive spot (29 + 1) |
| COL | 33 | 32 | 1 | 0 | 4 | +2, not settled |
| ESS | 32 | 30 | 2 | 0 | 0 | Matches |
| FRE | 31 | 30 | 1 | 0 | 2 | Matches |
| GEE | 34 | 30 | 1 | 3 | 3 | Matches |
| GCS | 33 | 32 | 1 | 0 | 0 | +2, not settled |
| GWS | 31 | 30 | 1 | 0 | 1 | Matches |
| HAW | 32 | 30 | 2 | 0 | 0 | Matches |
| MEL | 34 | 30 | 3 | 1 | 1 | Matches |
| NTH | 31 | 30 | 1 | 0 | 0 | Matches |
| PAD | 33 | 30 | 2 | 1 | 0 | Matches |
| RIC | 32 | 30 | 0 | 2 | 1 | Matches |
| STK | 35 | 30 | 1 | 4 | 0 | Matches |
| SYD | 32 | 30 | 2 | 0 | 1 | Matches |
| WCE | 34 | 30 | 3 | 1 | 0 | Matches |
| WBD | 31 | 30 | 1 | 0 | 0 | Matches |

## Sources by club

Every club used the same four kinds of source. The AFL feed and Footyinfo were read for every player; Wikipedia's list covers nearly all of them.

- **AFL public squad feed:** `https://aflapi.afl.com.au/afl/v2/squads?teamId=<id>&compSeasonId=96&pageSize=100`. Name, jumper, position, birth date, height, recruited from.
- **Footyinfo:** `https://www.footyinfo.com/team/<club>-aflw`. Age to the day, height, games, goals, recruited from, draft year and pick.
- **Wikipedia list template**, the last revision before 27 October 2026 for the in-season list, plus the latest for who has left since. Also player biographies, and the draft pages for 2016 to 2025 and the 2025-26 and 2026-27 movement pages.
- **AFL articles:** [list changes](https://www.afl.com.au/news/1542102), [top-ups](https://www.afl.com.au/news/1606963), [St Kilda top-up and Xenos](https://www.afl.com.au/news/1620246), [Morris-Dalton](https://www.afl.com.au/news/1572403), plus [Carlton's own report](https://www.carltonfc.com.au/news/2084174).

The official AFL team pages and club websites show exactly the same names as the feed, so I do not count them as a separate check.

| Club | AFL feed id | Footyinfo | Wikipedia template (in-season revision date) |
| --- | --: | --- | --- |
| ADE | 19 | [adelaide-aflw](https://www.footyinfo.com/team/adelaide-aflw) | Adelaide Football Club AFL Women's personnel (2026-10-20) |
| BRL | 21 | [brisbane-aflw](https://www.footyinfo.com/team/brisbane-aflw) | Brisbane Football Club AFL Women's personnel (2026-10-20) |
| CAR | 22 | [carlton-aflw](https://www.footyinfo.com/team/carlton-aflw) | Carlton Football Club AFL Women's personnel (2026-10-07) |
| COL | 24 | [collingwood-aflw](https://www.footyinfo.com/team/collingwood-aflw) | Collingwood Football Club AFL Women's personnel (2026-10-21) |
| ESS | 118 | [essendon-aflw](https://www.footyinfo.com/team/essendon-aflw) | Essendon Football Club AFL Women's personnel (2026-10-08) |
| FRE | 25 | [fremantle-aflw](https://www.footyinfo.com/team/fremantle-aflw) | Fremantle Football Club AFL Women's personnel (2026-10-08) |
| GEE | 26 | [geelong-aflw](https://www.footyinfo.com/team/geelong-aflw) | Geelong Football Club AFL Women's personnel (2026-10-08) |
| GCS | 33 | [gold-coast-aflw](https://www.footyinfo.com/team/gold-coast-aflw) | Gold Coast Suns AFL Women's personnel (2026-10-09) |
| GWS | 28 | [gws-giants-aflw](https://www.footyinfo.com/team/gws-giants-aflw) | Greater Western Sydney Giants AFL Women's personnel (2026-10-17) |
| HAW | 119 | [hawthorn-aflw](https://www.footyinfo.com/team/hawthorn-aflw) | Hawthorn Football Club AFL Women's personnel (2026-10-17) |
| MEL | 29 | [melbourne-aflw](https://www.footyinfo.com/team/melbourne-aflw) | Melbourne Football Club AFL Women's personnel (2026-10-17) |
| NTH | 30 | [north-melbourne-aflw](https://www.footyinfo.com/team/north-melbourne-aflw) | North Melbourne Football Club AFL Women's personnel (2026-10-18) |
| PAD | 120 | [port-adelaide-aflw](https://www.footyinfo.com/team/port-adelaide-aflw) | Port Adelaide Football Club AFL Women's personnel (2026-10-18) |
| RIC | 34 | [richmond-aflw](https://www.footyinfo.com/team/richmond-aflw) | Richmond Football Club AFL Women's personnel (2026-10-18) |
| STK | 36 | [st-kilda-aflw](https://www.footyinfo.com/team/st-kilda-aflw) | St Kilda Football Club AFL Women's personnel (2026-10-18) |
| SYD | 121 | [sydney-aflw](https://www.footyinfo.com/team/sydney-aflw) | Sydney Swans AFL Women's personnel (2026-10-18) |
| WCE | 35 | [west-coast-aflw](https://www.footyinfo.com/team/west-coast-aflw) | West Coast Eagles AFL Women's personnel (2026-10-20) |
| WBD | 32 | [western-bulldogs-aflw](https://www.footyinfo.com/team/western-bulldogs-aflw) | Western Bulldogs AFL Women's personnel (2026-10-20) |

## How far each check reached

- **Birth date:** 302 players have all three sources. The others have the AFL feed and Footyinfo, except 17 players Footyinfo gives no age for, who have one source at most. Footyinfo's date is worked out from its age in years and days, which fits the feed exactly for all but a couple of dozen players.
- **Height:** all three where a biography exists, otherwise two.
- **Games and goals:** Footyinfo is the only source for the current totals. Its before-this-season and this-season figures add up to its career figure for every player. Wikipedia could check 47 players whose biography is stated to the end of 2025; other biographies stop at an earlier or unstated point, so were not compared. **Most games and goals figures therefore rest on one source.**
- **Draft:** 346 Footyinfo draft entries were compared with Wikipedia's draft pages or biographies. Anyone else with a draft entry has Footyinfo alone.
- **Who is on the list:** every club against the AFL feed, Footyinfo and Wikipedia.

## Not settled

- **Collingwood and Gold Coast show 32 active, not 30.** Wikipedia's main lists hold 32 at both, and the AFL feed and Footyinfo agree on the names. No source I read says which two were not active or why. Three Gold Coast players have no 2026 game (Jamie Stanton, Sienna McMullen, Nyalli Milne), which is a lead only. All stay marked active as the sources show them.
- **Possible top-ups:** these rows are state-league players with high jumpers, on the AFL feed but not Wikipedia, and I found no announcement: Geelong's Simone Nalder, Mekah Morrissy, Lilly-Ann Ryder; St Kilda's Jordan Membrey, Amelia Peck, Lily Skinner; Melbourne's Tylah Burn; Richmond's Alana Barba, Caitlin Thorne; Port Adelaide's Aoife Berry. They are labelled "possible top-up, not confirmed". Confirmed: St Kilda's Zoe Barbakos and West Coast's Lisa Steane.
- **Nell Morris-Dalton (Carlton)** replaced the injured Maddy Guerin and played 13 games this year. Wikipedia's list has neither fact. An AFL piece gives her 41 career games across three clubs where Carlton gives 38 across two; this looks like timing.
- **Inactive, sources differ:** the AFL's July article has Carlton's Guerin, Essendon's Bess Keaney and St Kilda's Nicola Xenos inactive, while Wikipedia lists them as active. Xenos was later named an emergency, so she may have come back. Those rows say which source says what, where the status differs.
- **Name clash:** Collingwood's draftee Amy Smith and North Melbourne's Amy Smith are two people.
- **Left since the season:** "off the Wikipedia list" means only that. I did not check each reason, including Brooke Smith and Bella Smith, whose retirement line could not be tied to one club with certainty.

## Left out of the CSV

| Club | Player | Why |
| --- | --- | --- |
| ADE | Chelsea Randall | On the AFL feed; retired before the season (AFL article 1542102) |
| GWS | Claire Ransom | On the AFL feed; retired before the season (AFL article 1542102) |
| GWS | Katherine Smith | On the AFL feed; retired before the season (AFL article 1542102) |
| HAW | Aileen Gilroy | On the AFL feed; retired before the season (AFL article 1542102) |
| HAW | Kayley Kavanagh | On Footyinfo only: no jumper, 0 games for this club in 2026 |
| MEL | Jemmika Douglas | On Footyinfo's Melbourne page with no jumper. The AFL feed has her at Adelaide, and she is in the CSV there. Footyinfo credits the same 11 games of 2026 to both pages. |
| MEL | Alice Robinson | On Footyinfo only: no jumper, 0 games for this club in 2026 |
| SYD | Grace Hill | On Footyinfo only: no jumper, 0 games for this club in 2026 |
| WCE | Sophie McDonald | On the AFL feed; retired before the season (AFL article 1542102) |
| WCE | Jayme Harken | On Footyinfo only: no jumper, 0 games for this club in 2026 |
| WCE | Ruby Sargent-Wilson | On Footyinfo only: no jumper, 0 games for this club in 2026 |

The Footyinfo-only players may be post-season moves. I could not verify that.

## Disagreements

### Birth dates

`dob` is blank for each of these.

| Club | Player | Dates |
| --- | --- | --- |
| ADE | Danielle Ponter | AFL feed 2000-01-08; Footyinfo (from age) 2000-08-01; Wikipedia 2000-01-08 |
| COL | Eliza James | AFL feed 2003-10-13; Footyinfo (from age) 2003-10-01; Wikipedia 2003-10-01 |
| COL | Brittany Bonnici | AFL feed 1997-03-08; Footyinfo (from age) 1997-03-08; Wikipedia 1997-08-03 |
| ESS | Brooke Walker | AFL feed 1995-01-03; Footyinfo (from age) 1995-04-17; Wikipedia 1995-01-03 |
| FRE | Megan Kauffman | AFL feed 1997-03-21; Footyinfo (from age) 1997-03-21; Wikipedia 1997-03-22 |
| GEE | Chloe Scheer | AFL feed 1999-10-07; Footyinfo (from age) 1999-09-07; Wikipedia 1999-10-07 |
| GCS | Anne Hatchard | AFL feed 1998-07-03; Footyinfo (from age) 1998-03-07; Wikipedia 1998-03-07 |
| GCS | Charlie Rowbottom | AFL feed 2003-10-22; Footyinfo (from age) 2003-01-22; Wikipedia 2003-01-22 |
| GWS | Eleanor Brown | AFL feed 2000-01-21; Footyinfo (from age) 2000-01-20; Wikipedia 2000-01-20 |
| GWS | Daisy Walker | AFL feed 2002-06-04; Footyinfo (from age) 2002-06-06; Wikipedia 2002-06-04 |
| GWS | Emily Pease | AFL feed 2002-06-11; Footyinfo (from age) 2002-12-06 |
| HAW | Mackenzie Eardley | AFL feed 2004-01-13; Footyinfo (from age) 2004-05-30 |
| HAW | Jacqueline Dupuy | AFL feed 1994-07-19; Footyinfo (from age) 1994-07-19; Wikipedia 1994-07-09 |
| MEL | Kate Hore | AFL feed 1995-03-25; Footyinfo (from age) 1995-03-25; Wikipedia 1995-03-26 |
| PAD | Ellie Hampson | AFL feed 2001-08-02; Footyinfo (from age) 2001-02-08; Wikipedia 2001-02-08 |
| PAD | Caitlin Wendland | AFL feed 2003-09-13; Footyinfo (from age) 2003-09-03 |
| RIC | Laura McClelland | AFL feed 2001-07-03; Footyinfo (from age) 2001-07-03; Wikipedia 2001-03-07 |
| RIC | Dana East | AFL feed 2002-06-10; Footyinfo (from age) 2002-10-06; Wikipedia 2002-06-10 |
| RIC | Charli Wicksteed | AFL feed 2002-11-04; Footyinfo (from age) 2002-04-11 |
| STK | Nicola Barr | AFL feed 1996-06-03; Footyinfo (from age) 1996-06-03; Wikipedia 1996-06-13 |
| STK | Sophie Butterworth | AFL feed 2005-12-11; Footyinfo (from age) 2005-11-12 |
| SYD | Ash Van Loon | AFL feed 2004-08-11; Footyinfo (from age) 2004-08-11; Wikipedia 2004-12-08 |
| WCE | Charlotte Thomas | AFL feed 2003-05-09; Footyinfo (from age) 2003-09-05; Wikipedia 2003-09-05 |
| WCE | Mikayla Western | AFL feed 1998-01-07; Footyinfo (from age) 1998-07-01; Wikipedia 1998-07-01 |
| WBD | Deanna Berry | AFL feed 1998-05-07; Footyinfo (from age) 1998-07-05; Wikipedia 1998-05-07 |

Many are the day and month swapped, which suggests data entry rather than different people.

### Draft

The draft columns are blank for each of these.

| Club | Player | Footyinfo | Wikipedia |
| --- | --- | --- | --- |
| COL | Airlie Runnalls | 2021 #44 | draft pages: 2023 pick 54 |
| GWS | Poppy Boltz | 2023 #17 | biography: 2023 pick 19 |
| WBD | Isabelle Pritchard | 2020 #16 | biography: 2020 pick 11 |
| WBD | Rylie Wilcox | 2022 #21 | biography: 2022 pick 22 |

Not a disagreement: Footyinfo dates the pre-season draft 2026 and Wikipedia files it on its 2025 draft page. It was held on 4 May 2026, and the picks agree.

### Games and goals

`gm` and `gl` are blank for each of these.

| Club | Player | Footyinfo | Wikipedia |
| --- | --- | --- | --- |
| HAW | Kaitlyn Ashmore | before 2026: 91 games, 31 goals | to end of 2025: 101 games, 35 goals |
| NTH | Eilish Sheerin | before 2026: 41 games, 10 goals | to end of 2025: 43 games, 10 goals |
| PAD | Ashleigh Woodland | before 2026: 75 games, 71 goals | to end of 2025: 75 games, 61 goals |
| RIC | Paige Scott | before 2026: 40 games, 15 goals | to end of 2025: 39 games, 15 goals |
| SYD | Alexia Hamilton | before 2026: 42 games, 6 goals | to end of 2025: 43 games, 6 goals |

### Heights

108 players. `height_cm` is blank for each. Most differ by 1 or 2 cm, a few by more.

| Club | Player | Heights (cm) |
| --- | --- | --- |
| ADE | Sarah Allan | AFL feed 185; Footyinfo 178; Wikipedia 178 |
| ADE | Danielle Ponter | AFL feed 170; Footyinfo 161; Wikipedia 161 |
| ADE | Grace Egan | AFL feed 169; Footyinfo 169; Wikipedia 170 |
| ADE | Madison Newman | AFL feed 168; Footyinfo 168; Wikipedia 170 |
| ADE | Caitlin Gould | AFL feed 182; Footyinfo 182; Wikipedia 181 |
| ADE | Kiera Mueller | AFL feed 165; Footyinfo 165; Wikipedia 167 |
| ADE | Lily Tarlinton | AFL feed 186; Footyinfo 186; Wikipedia 180 |
| ADE | Grace Kelly | AFL feed 175; Footyinfo 175; Wikipedia 176 |
| ADE | Hannah Ewings | AFL feed 168; Footyinfo 168; Wikipedia 167 |
| BRL | Natalie Grider | AFL feed 166; Footyinfo 171; Wikipedia 171 |
| BRL | Sophie Conway | AFL feed 176; Footyinfo 170; Wikipedia 170 |
| BRL | Orla O'Dwyer | AFL feed 173; Footyinfo 173; Wikipedia 175 |
| BRL | Dakota Davidson | AFL feed 181; Footyinfo 181; Wikipedia 180 |
| BRL | Shanae Davison | AFL feed 164; Footyinfo 164; Wikipedia 167 |
| BRL | Eleanor Hartill | AFL feed 185; Footyinfo 186; Wikipedia 185 |
| BRL | Lilly Baker | AFL feed 180; Footyinfo 179 |
| BRL | Olivia Lacy | AFL feed 166; Footyinfo 169 |
| CAR | Gabriella Pound | AFL feed 163; Footyinfo 166; Wikipedia 166 |
| CAR | Claudia Whitfort | AFL feed 171; Footyinfo 170; Wikipedia 171 |
| CAR | Mimi Hill | AFL feed 165; Footyinfo 166; Wikipedia 166 |
| CAR | Yasmin Duursma | AFL feed 175; Footyinfo 174; Wikipedia 175 |
| CAR | Brooke Vickers | AFL feed 173; Footyinfo 171 |
| CAR | Brooke Boileau | AFL feed 169; Footyinfo 169; Wikipedia 170 |
| CAR | Darcy Vescio | AFL feed 166; Footyinfo 166; Wikipedia 167 |
| COL | Brianna Davey | AFL feed 175; Footyinfo 171 |
| COL | Tarni White | AFL feed 166; Footyinfo 170; Wikipedia 166 |
| COL | Kalinda Howarth | AFL feed 169; Footyinfo 167; Wikipedia 169 |
| COL | Airlie Runnalls | AFL feed 163; Footyinfo 164; Wikipedia 164 |
| ESS | Stephanie Cain | AFL feed 168; Footyinfo 169; Wikipedia 168 |
| ESS | Georgia Clarke | AFL feed 170; Footyinfo 177; Wikipedia 177 |
| ESS | Maddison Gay | AFL feed 166; Footyinfo 166; Wikipedia 168 |
| ESS | Bess Keaney | AFL feed 174; Footyinfo 173; Wikipedia 174 |
| ESS | Brooke Walker | AFL feed 171; Footyinfo 171; Wikipedia 173 |
| ESS | Georgia Nanscawen | AFL feed 162; Footyinfo 160 |
| FRE | Sarah Verrier | AFL feed 168; Footyinfo 168; Wikipedia 166 |
| FRE | Mim Strom | AFL feed 182; Footyinfo 182; Wikipedia 184 |
| FRE | Mia Anderson | AFL feed 169; Footyinfo 171 |
| FRE | Orlagh Lally | AFL feed 170; Footyinfo 170; Wikipedia 172 |
| FRE | Kiara Bowers | AFL feed 164; Footyinfo 164; Wikipedia 170 |
| GEE | Mikayla Bowen | AFL feed 163; Footyinfo 163; Wikipedia 164 |
| GEE | Jasmin Stewart | AFL feed 168; Footyinfo 167; Wikipedia 167 |
| GEE | Nicola Stevens | AFL feed 174; Footyinfo 173; Wikipedia 174 |
| GCS | Elise Barwick | AFL feed 169; Footyinfo 168 |
| GCS | Katie Lynch | AFL feed 180; Footyinfo 179; Wikipedia 179 |
| GCS | Charlie Rowbottom | AFL feed 179; Footyinfo 179; Wikipedia 180 |
| GCS | Ava Usher | AFL feed 162; Footyinfo 162; Wikipedia 165 |
| GCS | Lily Mithen | AFL feed 158; Footyinfo 159; Wikipedia 159 |
| GWS | Rebecca Beeson | AFL feed 165; Footyinfo 166; Wikipedia 165 |
| GWS | Tilly Lucas-Rodd | AFL feed 163; Footyinfo 160; Wikipedia 160 |
| GWS | Alyce Parker | AFL feed 165; Footyinfo 164; Wikipedia 164 |
| GWS | Tarni Evans | AFL feed 178; Footyinfo 178; Wikipedia 180 |
| GWS | Sophia Gaukrodger | AFL feed 172; Footyinfo 174 |
| HAW | Najwa Allen | AFL feed 173; Footyinfo 173; Wikipedia 177 |
| MEL | Olivia Purcell | AFL feed 161; Footyinfo 161; Wikipedia 164 |
| MEL | Tahlia Fellows | AFL feed 167; Footyinfo 169 |
| MEL | Blaithin Mackin | AFL feed 170; Footyinfo 170; Wikipedia 181 |
| MEL | Tayla Harris | AFL feed 177; Footyinfo 179; Wikipedia 177 |
| NTH | Emma King | AFL feed 184; Footyinfo 187; Wikipedia 187 |
| NTH | Tahlia Randall | AFL feed 173; Footyinfo 173; Wikipedia 175 |
| NTH | Kate Shierlaw | AFL feed 182; Footyinfo 182; Wikipedia 186 |
| NTH | Libby Birch | AFL feed 175; Footyinfo 175; Wikipedia 176 |
| NTH | Ash Riddell | AFL feed 158; Footyinfo 159; Wikipedia 158 |
| NTH | Nicole Bresnehan | AFL feed 165; Footyinfo 168; Wikipedia 168 |
| NTH | Tessa Boyd | AFL feed 173; Footyinfo 175 |
| NTH | Eilish Sheerin | AFL feed 174; Footyinfo 174; Wikipedia 175 |
| NTH | Erika O'Shea | AFL feed 167; Footyinfo 167; Wikipedia 181 |
| NTH | Emma Kearney | AFL feed 165; Footyinfo 167; Wikipedia 165 |
| PAD | Ashleigh Woodland | AFL feed 176; Footyinfo 173; Wikipedia 176 |
| PAD | Lucy Boyd | AFL feed 173; Footyinfo 172 |
| RIC | Kate Dempsey | AFL feed 164; Footyinfo 160; Wikipedia 160 |
| RIC | Beth Lynch | AFL feed 166; Footyinfo 173; Wikipedia 173 |
| RIC | Emelia Yassir | AFL feed 159; Footyinfo 159; Wikipedia 160 |
| RIC | Laura McClelland | AFL feed 174; Footyinfo 172; Wikipedia 172 |
| RIC | Rebecca Miller | AFL feed 185; Footyinfo 184; Wikipedia 184 |
| RIC | Gabby Seymour | AFL feed 176; Footyinfo 175; Wikipedia 175 |
| STK | Nicola Barr | AFL feed 169; Footyinfo 168; Wikipedia 168 |
| STK | Jordan Membrey | AFL feed 178; Footyinfo 169 |
| STK | Jesse Tawhiao-Wardlaw | AFL feed 187; Footyinfo 185; Wikipedia 185 |
| STK | Darcy Guttridge | AFL feed 168; Footyinfo 171; Wikipedia 169 |
| STK | Rene Caris | AFL feed 185; Footyinfo 184; Wikipedia 184 |
| STK | Georgia Patrikios | AFL feed 170; Footyinfo 169; Wikipedia 169 |
| STK | Olivia Vesely | AFL feed 167; Footyinfo 166; Wikipedia 166 |
| STK | Serene Watson | AFL feed 176; Footyinfo 174; Wikipedia 174 |
| STK | Molly McDonald | AFL feed 168; Footyinfo 167; Wikipedia 167 |
| STK | Hannah Priest | AFL feed 167; Footyinfo 168; Wikipedia 168 |
| STK | Tyanna Smith | AFL feed 169; Footyinfo 169; Wikipedia 167 |
| STK | Ashleigh Richards | AFL feed 170; Footyinfo 167 |
| STK | Nicola Xenos | AFL feed 160; Footyinfo 161; Wikipedia 161 |
| STK | Alice Burke | AFL feed 165; Footyinfo 162; Wikipedia 167 |
| STK | Charlotte Baskaran | AFL feed 161; Footyinfo 165 |
| STK | J'Noemi Anderson | AFL feed 171; Footyinfo 174 |
| STK | Paige Trudgeon | AFL feed 181; Footyinfo 180 |
| STK | Emmelie Fiedler | AFL feed 186; Footyinfo 186; Wikipedia 187 |
| STK | Bianca Jakobsson | AFL feed 176; Footyinfo 179; Wikipedia 174 |
| SYD | Brenna Tarrant | AFL feed 173; Footyinfo 173; Wikipedia 174 |
| SYD | Ally Morphett | AFL feed 188; Footyinfo 188; Wikipedia 190 |
| SYD | Montana Ham | AFL feed 179; Footyinfo 179; Wikipedia 180 |
| SYD | Ash Van Loon | AFL feed 174; Footyinfo 169; Wikipedia 169 |
| WCE | Lisa Steane | AFL feed 166; Footyinfo 165 |
| WCE | Isabella Shannon | AFL feed 177; Footyinfo 177; Wikipedia 178 |
| WCE | Amy Franklin | AFL feed 180; Footyinfo 180; Wikipedia 178 |
| WBD | Elle Bennetts | AFL feed 175; Footyinfo 172; Wikipedia 175 |
| WBD | Mikala Cann | AFL feed 170; Footyinfo 173; Wikipedia 173 |
| WBD | Jess Fitzgerald | AFL feed 163; Footyinfo 163; Wikipedia 176 |
| WBD | Sarah Hartwig | AFL feed 173; Footyinfo 173; Wikipedia 174 |
| WBD | Ellie Gavalas | AFL feed 158; Footyinfo 158; Wikipedia 160 |
| WBD | Jasmyn Smith | AFL feed 165; Footyinfo 159; Wikipedia 158 |
| WBD | Louise Stephenson | AFL feed 178; Footyinfo 176; Wikipedia 178 |

### Name spellings

The CSV uses the AFL feed's spelling. Most of these are a short name against a full name.

| Club | AFL feed | Other source | Their spelling |
| --- | --- | --- | --- |
| ADE | Madison Newman | Wikipedia | Maddi Newman |
| BRL | Alexandra Anderson | Wikipedia | Ally Anderson |
| BRL | Isabel Dawes | Wikipedia | Belle Dawes |
| BRL | Natalie Grider | Wikipedia | Nat Grider |
| BRL | Catherine Svarc | Wikipedia | Cathy Svarc |
| CAR | Gabriella Pound | Wikipedia | Gab Pound |
| CAR | Madeleine Guerin | Wikipedia | Maddy Guerin |
| COL | Ashley Centra | Wikipedia | Ash Centra |
| COL | Lucille Cronin | Wikipedia | Lucy Cronin |
| ESS | Stephanie Cain | Wikipedia | Steph Cain |
| ESS | Madison Prespakis | Wikipedia | Maddy Prespakis |
| ESS | Maddison Gay | Wikipedia | Maddi Gay |
| ESS | Alexandra Morcom | Wikipedia | Alex Morcom |
| ESS | Stephanie Wales | Wikipedia | Steph Wales |
| FRE | Gabrielle Newton | Wikipedia | Gabby Newton |
| FRE | Angelique Stannett | Wikipedia | Ange Stannett |
| FRE | Madeleine Scanlon | Wikipedia | Madi Scanlon |
| GEE | Jacqueline Parry | Wikipedia | Jackie Parry |
| GEE | Alexis Gregor | Wikipedia | Lexi Gregor |
| GWS | Brodee Mowbray | Wikipedia | Brodie Mowbray |
| HAW | Laura Elliott | Wikipedia | Laura Elliot |
| HAW | Jacqueline Dupuy | Wikipedia | Jacqui Dupuy |
| MEL | Shelley Heath-Barker | Wikipedia | Shelley Heath |
| MEL | Jordyn S. Allen | Footyinfo | Jordyn Allen |
| MEL | Jordyn S. Allen | Wikipedia | Jordyn Allen |
| RIC | Mackenzie Ford | Wikipedia | Mckenzie Ford |
| SYD | Jas Grierson | Wikipedia | Jasmine Grierson |
| SYD | Alexia Hamilton | Wikipedia | Lexi Hamilton |
| SYD | Ash Van Loon | Wikipedia | Ashleigh Van Loon |
| WCE | Roxanne Roux | Wikipedia | Roxy Roux |
| WCE | Isabella Lewis | Wikipedia | Bella Lewis |
| WCE | Charlotte Thomas | Wikipedia | Charlie Thomas |
| WCE | Jessica Rentsch | Wikipedia | Jess Rentsch |
| WBD | Vaomua Laloifi | Wikipedia | Mua Laloifi |
| WBD | Keeley Hardingham | Wikipedia | Keely Hardingham |
| WBD | Analea McKee | Wikipedia | Analee Mckee |

### A Wikipedia page that is someone else

- COL Jemma Rigoni: the page "Jemma Rigoni" has a birth date of 1974-07-27 and a career ending 2005, so it is a different person. I ignored it.

## Gaps

Blank fields in the 585 rows:

| Field | Blank | Why |
| --- | --: | --- |
| `dob` | 25 | Sources disagree |
| `age` | 17 | Footyinfo shows a dash for these players |
| `height_cm` | 108 | Sources disagree |
| `gm`, `gl` | 5 | Sources disagree |
| `draft_year`, `draft_pick` | 180 | No draft entry on Footyinfo (signings, rookies, free agents), or sources disagree |
| `how_joined_club` | 254 | No entry for that player and club on the pages read |
| `list` | 13 | Top-ups and replacements not on Wikipedia's list |

Jumper, position, recruited from and list status are filled for every row.
