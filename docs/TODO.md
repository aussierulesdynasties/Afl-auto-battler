# TODO: everything not done yet

The one list of work not done. Point a session at this file and it works down it. Done and cut items are removed after merge from the PR's `Closes row N` line (git history keeps them). Director rulings live in `docs/DIRECTOR_BIBLE.md` (reference, not a work list); the later ruling wins. Balance is the director's call. There are no feature switches (director 2026-11-06): work goes straight into the game and his playtest judges it (section B). Updated 2026-11-10 against main `eda15c51`: every row checked against merged work. Work it in the order of the "Order of work" section below; a row starts when everything in its "After:" note is done. Audits and balance wait in section Z (director 2026-11-10). Live on itch: 1.0.13 (976718a).

## Itch builds

Which build goes to itch next, and when, is in `docs/ITCH_BUILDS.md` (read it only for a release).

## Order of work (dependency order, 2026-11-10)

A row starts when everything in its "After:" note is done. Rows in the same step run side by side, except rows that edit the same file, which merge one at a time: `tools/lint/copy_voice.py` (its ALLOW counts are exact), `GameState.gd`, `UiKit.gd`, `StoppageVignette.gd`, and the figure shader and sheets.

1. Put the waiting looks and questions to the director (sections C and H, the 6.34 captures, the hair contact sheets). Start the rows with nothing to wait for: 6.40, 6.42, 6.53, V2, V9. The director's playtests in section B can happen at any time.
2. The rest of T1.R26; V4; 134 and 135 (after 150); the row 34 re-check; 164 (its PR is in flight).
3. 131 (after T1.R26 and 151); 136, 137 and 138; 139; V5; the P-43 press slice of T7.R87; T8.Q20; 6.38.
4. 132, then 161 (row 9's feed colours); T2.25; 140; 6.63; 32, then 128 (both change the save, so one at a time); T8.78 after 128. The director looks at 5 and 16 and playtests 13, 14 and 15.
5. 133; V6; 6.58; 159 (after T8.Q20); 160; 162; 163. The director playtests 10 and 35/36.
6. 144; the rest of T3.R9; 6.49, then the rest of T7.R87 (both edit MatchScene.gd); 6.64.
7. The director's final looks and playtests (9, 49/50, 24, 26); V8; 56. Every row outside section Z closes before Z starts.
8. Section Z: 11/T2.29, then T2.31 (both edit MatchSim.gd); Custom plan; Synergy; 30; the T2.25 lanes audit; Z67; the 6.53 phone numbers.
9. Balance; T8.50; T8.83.
10. T8.88; 28; T8.87; then 42 is measured again for the director's ruling.
11. 58/39 dial sizes, then the director's playtest. That closes the list.

The longest chain, which sets the finish: T1.R26, then 131, then the director's look at 5, then 133, then T3.R9, then the final looks, then Custom plan, then Balance, then T8.88, then 58/39. A delay in T1.R26 or 131 delays everything after it.

## A. Build now (open, no blocker, order = story first, then sim, then approachable)

| # | What | Done looks like |
|---|---|---|
| 179 | FIRST, game-breaking (director 2026-11-12, 1.0.15: "im still doing shepparton trades too, so the game is fundamentally broken, huge bug"; "i got sacked from shepparton and yet im still picking their replacement coaches"). After a sacking the coach still runs the old club: Staff shows Shepparton with "Senior coach: You" and Appoint, and its trades are his. Every club call (staff, trades, list, selection) follows the new club, or none. | test: sacked coach makes no call for the old club |
| 142 | Legacy mode, first slice 1990 (director 2026-11-11: "id like you to start building the legacy mode starting 1990 now too"; replaces the parked 2010 first slice). Start dates in the end (director 2026-11-11: "in the end id like players to be able to pick the following start dates: 1990, 2000, 2010, 2020, current season, 2028 (tassie), 2030 (canberra)"): seven starts. The four past ones run on that era's real lists; the current season is today's start; 2028 is the Tasmania start that already exists (2027 plays without you, row 129); 2030 starts with Canberra entering, its enter year already set in clubs.csv, on the same pattern. 1990 is built first. Director 2026-11-11: data for 1990, 2000, 2010 and 2020 is gathered now, and "once you gather all the data, start putting it into the game". His answers the same day (Director Bible, legacy rulings): the Fitzroy merger always happens unless you are a regular finalist (then a slim chance it still does); real controversy penalties land, behind one on/off switch at game creation; personal-conduct events name the club only; era grounds and guernseys are in the 1990 slice. "all guernseys need a 90s and 2000s and 2010s version too": every club gets a guernsey for each of those decades. Watch (director 2026-11-11: "if the playing data for historical decades is significantly different in its averages and is subsequently overrating/underrating the players, let me know, keep an eye on it" / "because the game of AFL has changed dramatically in those eras so the stats might be different"): each decade's rating build reports its stat averages against the 2026 base and the spread of ratings it produces (players rated 80+, list medians per club); if a decade's averages push ratings up or down away from the 2026 shape, tell the director with the numbers before it ships. His fallback (same day): "if the balance changes considerably from era to era we will have to create a clever inflation immune/era-scaling player rating". Ground names (director 2026-11-11: "note that the name of 'Marvel' stadium has changed regularly in the past 30 years, it must carry its IRL era-appropriate name / a short news story in the feed can commemorate when the names change"): Docklands carries its real name for the year (Colonial Stadium, Telstra Dome, Etihad Stadium, Marvel Stadium), and every other renamed ground does the same; a short news-feed story marks each change. Potential is informed (director 2026-11-11, "Informed"): a real player's real peak sets his ceiling, give or take luck. Money (director 2026-11-12, "Dollars of the time"): salaries, the cap and every money figure show in that season's dollars; the 1990-2012 salary cap figures are to be found, not left as gaps ("huh? look harder"). His rulings 2026-11-10 in the Director Bible: era-accurate drafts with the sim's picks (an alternative history), era rules arriving in the year they began, real historical events, ratings per era, play from 1990 to 2100 and beyond. Mostly data: each 1990 club's real list rated like the 2026 lists, and the 1990 league (14 clubs: Fitzroy and the Brisbane Bears; Adelaide 1991, Fremantle 1995, Port 1997). The 2010s data and its tools are in data/legacy/2010s and tools/legacy_2010s (#1324). State league results simulate very fast (row 128) applies to any era league too. | A career can start in 1990 at any of that year's clubs on its real list, rated per era, play the 1990 season in that year's league shape, and roll into 1991 with the real draft class entering (picks are the sim's); captures approved by the director |
| 156 | More colours in the Club Forge (director 2026-11-11: "also please add more colours to the Club Forge"). | The Forge offers a wider colour choice for guernsey and club colours; captures approved by the director |
| 157 | A bespoke event-card deck for each club (director 2026-11-11: "i want a bespoke deck of event cards unique to each club, at least 1 per season from 1990-present (though the event cards dont need to strictly be year appropriate, i just want 25ish cards for each club) / this includes Tasmania, Canberra and even Fitzroy and Brisbane"). About 25 cards for each of 22 clubs. Every campaign uses them (director 2026-11-11: "to be clear, i want a bespoke club specific deck for each club which can be used in all modern era campaigns as well"), and they are era agnostic (same day: "i think club decks should be era agnostic, but YEARs should also have their own bespoke events (if appropriate, not EVERY year)"): no club card depends on a year. Year events are a separate set, drawn from the 1990-2026 off-field dramas research (C:/kt/era_dramas), one or more for a season only where history gives one. Research drafts first, in C:/kt/club_decks (not in the repo). Personal conduct stays at club level; controversies sit behind the on/off switch (row 142). | Every club, in the 2026 career and every legacy start, including Tasmania, Canberra, Fitzroy and the Brisbane Bears, has about 25 cards of its own in the game, each effect following its premise; the director has read them |
| 154 | Medical retirement check for concussion (director 2026-11-11: "if a player gets 5 or more concussions within a 5 year period, they should have to pass a medical retirement check"; "Flat odds each time"; the panel sits "Straight after the fifth"). Every club. Built in PR #1402 (merged); its player-sheet concussion line approved (director 2026-11-12); the cleared chance is one number, first value 50%, his to tune. | A player with five or more concussions in five seasons faces the panel the week of each such concussion at one stated chance; a fail ends his career that week; the count and the odds show on his sheet before it happens; league-wide medical retirements measure above zero and at or under 0.25 a season in the T8.83 batch run ("its quite rare IRL too, maybe 0.25 per year or less", 2026-11-11), with the league concussion total and its balance screen reported; and the director approves the captures |
| 152 | Home grounds for the fictional and expansion clubs (row 6.44; director 2026-11-10): each plays at a real regional ground near its town, e.g. Bellerive or Manuka, with its own ground look. After: the director's look at the six no-name captures in 6.44 | each such club's home ground draws as its real regional ground in a match, and the director has looked |
| 131 | Copy voice pass 1, gates (with T1.R26): scripts/sim/GateOdds.gd, MatchSim.gd call cards, CoachReport.gd pep talks and plans; MatchSim's "He should kick it" After: T1.R26 and 151. | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tools/lint/copy_voice.py ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 132 | Copy voice pass 3, match view and feed: MatchScene.gd lines and the feed's punctuation; the feed keeps a broadcaster's voice and its "!" (director 2026-11-10, #1303). Row 9's feed colours are row 161 (our goals in our club's colour, not blue, per the 2026-11-10 ruling; goals against red; the rest grey). After: T1.R26 and 131 | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tools/lint/copy_voice.py ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 133 | Copy voice pass 4, breaks: MatchNotes.gd, CoachReport.gd break report, MatchStory.gd After: T1.R26, 131 and the director's look at 5. | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tools/lint/copy_voice.py ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 134 | Copy voice pass 5, team builder and coaching: SelectionScene.gd, CoachingScene.gd (payroll), the team and coaching intros; Auto-pick keeps its name (director 2026-11-12: "Auto pick. I already answered this question"; exempt from the engine-word ban) After: 150. | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tools/lint/copy_voice.py ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 135 | Copy voice pass 6, training: TrainingScene.gd After: 150. | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tools/lint/copy_voice.py ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 136 | Copy voice pass 7, draft and pre-season: DraftScene.gd (projection), PreSeasonScene.gd (10 "starter"), the draft and combine intros After: T1.R26. | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tools/lint/copy_voice.py ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 137 | Copy voice pass 8, contracts and trades: OffseasonScene.gd (payroll), Contracts.gd, DraftTradeSheet.gd, StaffScene.gd; the T3.R56 trade and contract tutorials (shipped in #1293) are rewritten in this voice After: T1.R26 and 150. | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tools/lint/copy_voice.py ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 138 | Copy voice pass 9, profile: PlayerSheet.gd, and GameState.gd's projection line After: 134. | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tools/lint/copy_voice.py ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 139 | Copy voice pass 10, stats and menus: stats screens, StatGuide.gd (projection), OptionsSheet.gd, ListScene.gd After: T7.R84, 145 and 149. | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tools/lint/copy_voice.py ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 140 | Copy voice pass 11, event cards and press: data/stories/*.json (four "should"), StoryEngine.gd, MediaConference.gd, PressScene.gd; the row 34 event-card sheet is rewritten here and shown to him After: the director's ruling on row 34 and the P-43 press slice of T7.R87. | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tools/lint/copy_voice.py ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 159 | Speed up the match engine (director 2026-11-12: "Speed up the engine"; drift "Inside AFL bands"). Unlike T8.Q20 (byte-identical weekly AI work), a speed-up here may shift stats, but only while every stat stays IN or NEAR the real AFL bands. After: T8.Q20. | a timed bench of weeks before and after; `tools/balance.sh match 1000` paired (main vs branch) with every stat IN or NEAR, table pasted in the PR |
| 160 | Weather can change at a break (director 2026-11-12: "Yes, at a break"). At most once a match, announced at a break; the pre-match forecast states the odds of a change. Every club plays under the same rule. | a seeded match where the weather changes at a break, with the announcement and the forecast odds shown; the rate of changes matches the stated odds on a seeded run; `tools/balance.sh match 1000` paired table in the PR |
| 161 | Feed colours (director 2026-11-10: "your club's colour, not blue"; re-asked in error 2026-11-12, he said "not sure, you choose", so the 11-10 ruling stands): our goals in our club's colour (his 2026-11-10 ruling, not blue), goals against red, everything else grey. After: 132. | the feed shows our goals in our club's colour, goals against red and every other line grey, with no blue; 390 px captures shown to the director |
| 162 | A vignette for every decision card (director 2026-11-12: "Yes, every card"; today only the centre ball-up has one, 2.Q12). Builds on row 13 (time pauses on a vignette at a decision). | every decision card opens on its own vignette, proven per card in a capture that shows the intended art loaded; captures shown to the director |
| 163 | Soften autopilot (director 2026-11-12: "Too harsh"): a club on autopilot drifts to mid-table, not last (today about 18th by year five). The same rule runs for every club. | a seeded multi-season audit (with the T8.83 batch) shows an autopilot club settling mid-table; managed clubs still do better |
| 174 | Ask-around answers: player names in club ink (director 2026-11-12: "sanders uncoloured?", Ryley Sanders plain in Essendon's offer). A fresh off-season probe inked every name; find the state that drops it. | test with that state |
| 175 | No trades for a called pick (director 2026-11-12: "why are adelaide trading for pick 42 if the pick already called"). | draft-night test: no trade names a used pick |
| 176 | Season review "Trade period": clubs and players in their colours (director 2026-11-12: "no colour coding on names"). | capture, every name inked |
| 177 | Ladder Rating is your best 23 (director 2026-11-12: "ladder should always show your best 23 rating"; preview said 9th, ladder equal last). Preview ranks Squad.strength; ladder averages OVR (TeamRating). | test: both agree |
| 178 | Tagging: their man's own touches (director 2026-11-12: "says 27 touches 100% of the time"). It is a constant, Roles.TAG_USUAL_TOUCHES. | test: two men, two numbers |
| 166 | Visuals 1, match day (director interview 2026-11-12, first): one replay stadium in every view; tight, full, moving call scenes; set shot by distance; one-screen pre-match; bigger discs, bench drawer; wind, hot, night; PC oval left, panels right; scoreboard and overlap bugs. Detail: Director Bible, "Visual overhaul interview". | one before-and-after look sheet, every frame self-checked, shown to the director |
| 167 | Visuals 2, event cards and press: chips, a picture per event, big finals cards; odds bars, journalist on screen, rules behind a tap, pictured result. | look sheet shown to the director |
| 168 | Visuals 3, hub and frame: checklist rows, stripes top only, club-colour buttons, row style, bigger and brighter small text, motion. | look sheet shown to the director |
| 169 | Visuals 4, money, draft, new career: cap meters and deal cards; draft list gets the screen, prospect bars, draft stage; jumper club picker, setup steps, press-room interview, coach card. | look sheet shown to the director |
| 170 | Visuals 5, season end, pre-season, ceremonies to the farewell's standard; then player faces and hair. | look sheet shown to the director |
| 171 | Visuals 6, proper PC layouts for every sheet. | 1920x1080 look sheet shown to the director |
| 172 | A Club Forge club can start a Real 2026 lists career as a new club with the new-club draft package every new club gets (director 2026-11-12: "Yes, as a new club"; widens ruling 71). | a real-lists career with a Forge club drafts its package; his playtest |
| 173 | In a 2027 League redraft, Tasmania joins in 2028, not round 1 of 2027 (director 2026-11-12: "Join in 2028"; PR #1172 had them from 2027). | 2027 ladder has 18 clubs, 2028 has 19 |

## B. Built and ON: his playtest judges

Every switch went on for good in #1072 and #1074 (director 2026-11-06: "i dont want any switches"). These are in the game and wait on his playtest; a row closes when it passes. The balance pass over the balance-gated rows is in section Z.

| # | Feature | PRs | Open |
|---|---|---|---|
| 129 | Tasmania on the AFL's real list rules (director 2026-11-09, "do it like this then", "Stars weigh it harder"): rivals' players rated 80+ will not join. Three test careers, 2028: 8-14, 4-18, 4-18 | 1184, 1187 | his playtest of the 2028 start, including the 80 (the agent's number, his to change) and building without the floating compensation year and lists of 48 |
| 61 | Weather: wet, wind and heat fitted to 2016-25 AFL games (live in 1.0.9). Balance stays his call; the look never touches the sim | #1150 #1089 #1084 | his playtest |
| 1 | Top three attributes on cards, Needs work benchmark, scout grade word for hidden prospects | #863 | his playtest, after row 150 (the compact cards show the top three) |
| 9 | Feed colours: your goals good, goals against bad, behinds and calls neutral | #918 | his playtest, after row 161 (our goals in our club's colour, goals against red, the rest grey) |
| 10 | Kick range caps receiver choice; Sim the week shares the same pick | #857 #879 | his playtest of an exported-PC full match: collection pauses and far receivers gone (about 12 long collects a match remain from other causes). After: T2.25 |
| 49, 50 | Match hero, turning point, reasons; club almanac | #853 #855 #890 | his playtest. After: 145, 144 and 133 |
| 35, 36 | Finals cards slice 2 and Grand Final cards | #864 | his playtest of the eight slice-2 cards (A3, A9, A14, A15, A16, B7, B8, B9), including the B8 running debt. After: the row 34 ruling and 140 |
| 52 | Expansion package, training report, speccy front | #711 #725 #735 #741 #1164 #1174 #745 #1126 #1074 | his playtest of the speccy front and the expansion entry; his look at the training report popup (#1164) |
| 13 | Every in-match decision opens on a vignette scene; time pauses at a decision | #902 #908 | his 1.11 playtest gate. After: T1.R26 and 131 |
| 14 | Opposition goal run as two football moves over the centre ball-up | #903 | his playtest; the two moves stand as built: Stack the centre bounce and Flood behind the ball (director 2026-11-10, D5 Q57). After: T1.R26 and 131 |
| 15 | Late-game centre ball-up: two distinct choices | #899 #1074 | his playtest, after row 151 (the two new moves) and copy pass 131 |
| 24 | Training as a compact player card grid with roles and traits | #928 | his playtest on his phone. After: 135, T3.R9 and 6.34 |
| 65 | Draftees start lower: picks 1-5 about 62, 6-20 about 56, POT kept (4.Q9) | #1031 #1050 | his playtest |
| 78 | Rare big margins come back through Momentum (T8.Q4) | #1029 #1038 | his playtest; balance in Z (row Balance). Director 2026-11-12: "the score is unrealistic" (125 to 20) |
| 89 | Midfield intercepts (T8.Q8) | #1024 | his playtest (measured about 2.58 a game against real 2.5; team intercepts 68.2 against about 63.4); balance in Z (row Balance) |
| 92 | Back-zone carries retuned (T9.Q22) | #1023 | his playtest; balance in Z (row Balance) |
| 103 | Synergies within reach on recruit screens; a stat focus grows a trait, for every club (4.Q10) | #1240 | his playtest; balance in Z (row Balance); numbers: Z, synergy numbers up |
| 158 | Custom game plan: the coach picks one strength and one cost, each moving real match stats; counters nothing; AI clubs build their own; the game-plan traits are gone | #1458 #1482 | his playtest; the sizes are first guesses, balance in Z (row Custom plan) |
| 164 | The draft needs list room: a full list must delist or trade before the draft starts, three players at least; rivals work to the same rule | #1443 #1470 #1482 | his playtest. Open faults: an upgrade during a paused draft can pass the 44; the expansion forced trade skips the 44 check |

## C. Needs his look or call (shown, then ask)

- 5 Defensive set-up break wording (merged by #874), after T1.R26 and 131. 16 PC bounce scene, after 6.38. 20 Press conference: the black bands were removed in #1120; his look at a capture, after 6.42.
- 7 Shake on his device. 26 Season stats hub phone review, after T3.R9 and 139.
- 34 62-line event-card copy sheet (docs/research/event_card_audit_2026-10-12.md): re-check it against the current deck (#1153 and #1205 changed lines and triggers), show him what still applies, record his ruling and apply it.
- 87 Turnover caption (#617) and the Bring the heat look: show him both again (T2.Q10).
- V0 What does 'beautiful' mean to you: which two or three screens from shipped games would you sit this game beside?

## E. Waiting on him or his phone

- 31 Native phone frame time, battery, loading (needs his phone; PC baseline only).
- 59 Banner text and music: he supplies originals (placeholders in `data/banners.json`, empty playlist).
- 56 Public demo page: rights to real names and a licence register come first.
- 32 Web build parity: saves carried between devices pending his answer.
- 113 Each club's real 2026 National Draft picks, with sources (parked, director 2026-11-10: "the draft hasnt happened yet so park it for now"). The rest shipped as the Real lists start (#569, #1172): real lists, the real 2026 class with ties, the 2026 National Draft, then 2027. Today the opening draft runs in reverse 2026 ladder order (GameState.gd begin_real_lists). Blocked until the real 2026 National Draft has happened.

## F. Later (1.x or after 1.0, unassigned)

- 38 Live-3D vignette probe (low priority; Tripo ruck rig in Godot).
- 43 More Tripo emblems (15,000 credits set aside; first slice done, none further assigned).
- 44 State of Origin (not for 1.0; scope interview first).
- 41 Club Forge game-plan builder.
- 143 Sandbox mode: every list and every player's numbers editable at any time (director 2026-11-10, parked). A separate mode, and the career wears a visible Sandbox mark so its honours and records don't read as earned (bible: the game is objective about risk). First slice: an Edit player sheet opened from a profile, built on Club Forge and the player Forge; phone first, no spreadsheet editor.
- 153 Stretch goal, the coach's phone (director 2026-11-11, not assigned): "smart phone/social media hub including contacts, a folder for players screenshots, perhaps a home for stats and news too". Scope interview first: what the contacts do, what the screenshot folder holds, and whether stats and news move there from the hub or are reached from both (one clear job per screen; the hub leads with events and the news ticker).
- 155 Stretch goal, Club Opinion (director 2026-11-11, not assigned): "like players have a unique opinion of you, clubs also could have, informed by how easy you were to deal with in trades, and through your reaction to existing cards (retune) and through bespoke Club Opinion cardset (not built)"; "Club Opinion is seperate to Board, and only applies to clubs other than the one you currently coach"; "Club Opinion will impact a clubs willingness to trade with you, or even employ you in the future, and lets leave its impact open ended to incorporate later features into it (perhaps we can build it into the phone Contacts feature, and build a contact list whose usefulness is gated by Club Opinion)". Three parts when assigned: the opinion itself, moved by trade dealings; a retune of existing cards so answers move it; a new Club Opinion card set. May feed the phone's contacts (row 153). Press too (director, same day): "club opinion will probably have to be tied into the press as well", so press conference answers about other clubs move it.
- 165 Draft preview in the news (director 2026-11-12, roadmap item, not assigned): "during the finals the news will put out an article predicting the top 10 draft picks in order (its never completely accurate)"; "each prediction will include a short bio of the player discussing their actual traits and skills". Bios state true traits and skills; only the order is a guess. Every club's coach reads the same article.
- T3.R41 Team selection as two screens on phone, side by side on PC, no scroll (ruled later, 2026-11-06).
- T3.R10 Accessibility, colour-blind kit-clash check (P-34: every disc pairing through deuteranopia and protanopia simulation, CI contrast floor) and text size on ground and vignette text (#1158 Q3); parked by the director 2026-11-10.
- Player personality types and captaincy meaning (composure, late-game stability): both wanted, later (T5.Q12, T5.Q13).
- Presentation wishlist: away/clash and heritage guernseys, coach appearance, premiership guernsey history, player card
  evolution, record-breaker marks, legends wall, draft class identity, archive gallery, retirement variants, dynamic
  crowd, season poster, stadium identity, user guernseys and logos, Coach of the Year.
- Deferred by ruling: announce the cap step, league rule changes. (Weather at a break is row 160, director 2026-11-12.)

## Working rules
- Godot runs off-screen with its own user data (`APPDATA=<scratch dir>`); kill only your own PIDs.
- Balance: screen every balance-gated row or match-engine change with `tools/balance.sh match 1000` (paired: main vs the branch, `--a-root <main checkout> --b ""`) before the PR and paste its table in the PR body; extend the harness rather than writing one-off probes (tools/balance/README.md).
- Run only the suites your change touches locally; CI runs the rest. Long audits go to `audit.yml`.
- Revert `.import` and `.uid` churn before committing. Stage by name; never `git add -A`.
- One worktree per session, from `origin/main`. Don't push to a PR branch while its CI runs unless the merge needs it.
- Never edit this file in a feature PR: write `Closes row N` (or `Closes rows 22, 27`, `Closes row T5.Q24`) in the PR body and `roadmap_close.yml` deletes the row after the merge. Edits to the list itself (new director requests, with his words) go in a PR labelled `roadmap`.

## G. From the Bible check (2026-11-04): open and not built

Ids point at `docs/DIRECTOR_BIBLE.md`. Verified against the code on 2026-11-04, re-checked against main on 2026-11-10 (#1278).

| Id | What | Done looks like |
|---|---|---|
| 128 | Stretch goal, a real state league (director 2026-11-08: "real VFL/seconds league with real rosters. players can choose to start their careers there and rise up the ranks. or can take a job at alower league if they lose their afl job and fight their way back"). Assigned 2026-11-10 ("Build it"); first slice to be put to him. Builds after T7.R84 and T8.Q20 (the same weekly sim loop). Already in the game to build on: the way-back story after a sacking, coaches' "Coaching in the state league" history, VFL clubs as prospect origins, the reserves. State league results simulate very fast (director 2026-11-11: "just make sure the state league results are simulated very fast"): every state league match except the coach's own uses a quick result model, not the full match engine; a whole state league round adds under 5% to Sim the week, measured. When the coach is coaching in the state league, it flips (director 2026-11-11: "if you are currently coaching in the VFL, the league simulation operates like normal. Contrarily, the AFLs simulation would then become minor background"): the state league plays like the AFL does now, and every AFL match uses the quick result model and sits in the background. Interview answers (director 2026-11-12): real names for the state leagues' own players, sourced like the AFL lists ("Real names"); the first slice has the VFL, SANFL and WAFL ("VFL, SANFL and WAFL"); an AFL club's players left out of its senior side play that week's state league match for its reserves or aligned side, with their own stats, form and injuries, and development comes from those games ("They play real VFL games"; supersedes rule 27's "no playable reserves competition"); a career can start at any state league club, AFL reserves sides included ("Every VFL club"). After: T8.Q20, T7.R84 and 32. | a career can start at a VFL club on sourced real lists and rise to an AFL job; a sacked coach can take a VFL job and fight back |
| T1.R26 | Finish the decision-transparency job on the gates still open: "I want full transparency behind each decision and the impact it will have"; "RNG is still okay, as long as the risks are clearly defined in the decision gate." Rulings 2026-11-10: "Gain / Cost everywhere" (odds inside the line); M1 "Gain for this list today" with the suits-it figure beside; L1 "Everything follows the read"; L2 "One scouting-budget line"; L4 "Costs in the rule's spirit" (morale, cap, legs, each sized); C1 "Cost sheet, one look". Done: M1, M2, M3, M5, M6 and the M7 set shot (#1317), C1 Tribunal cost sheet (#1336); S1, S2 and C2 (#1335) are met; L4 list costs is PR #1341, L1 and L2 are PR #1347, FA weights are PR #1348, L3 rival reads (free-agency odds and the Recruiting miss line) is PR #1397, approved and merged 2026-11-12. Gates to build, in this order (director 2026-11-10 left the order to Claude): M4 rotation sizes, the other M7 in-match cards and the list's dominant options. | Each listed gate shows a gain, a cost and its odds in the ruled label wording, and no gate is left with a dominant option; the C1 cost sheet gets his one look before it is built. |
| T2.25 | Kick lanes (M4-014): corridor, switch and down the line chosen by game plan in place of the random 10% switch. Director: "lanes are recorded and affect play, not presentation only." The old claude/kick-lanes branches are gone from origin and nothing is on main. Lanes audit in Z After: T8.85 and 131. | PR merged on green with the lane recorded per kick, play affected by plan and a motion clip of the three lanes. |
| T3.R9 | Readability sweep, one screen per PR in the order he sees them: hub, match view, breaks, team builder, training, draft, contracts and trades, profile, stats, menus. Then the match-view centrepiece pass ('looks like PowerPoint'). His words: "readability and intuitive interfaces are a core pillar of this project, paramount to its success". Batches 1 and 2 only partly cover stats and menus (390x844 and 1280x720, no record he looked). Hub done (story card text to body size, opponent lines in TEXT under their club's bar; `tools/visual/capture_sweep.gd`). Match view done, with its centrepiece pass (crowd in the stand, lit turf, shaded discs, light edge on dark kits, oval text at the 13 px floor, bigger PC score). Left: breaks, team builder, training, draft, contracts and trades, profile, stats, menus. After: V4 and V5; each screen after its copy pass (133 to 139). | Each screen has before/after captures at 390 and 1920 px that the director has looked at, and the match view has been reworked and shown to him. |
| 6.34 | Styling looks STYLE-01/03/04/05/06 (#1250-#1255): his verdict on each look, recorded (a look merged before approval needs it, or a revert). Missing captures: STYLE-05 headers on Main, STYLE-04 on the match oval (bible ruling 34), STYLE-03 on named screens; the Training rows fix (#1250). After: nothing; it needs the windowed-capture fault fixed first (UiKit, StoppageVignette and HubScene fail to compile in a windowed run). | Each look is shown to the director as a capture on those screens with his verdict recorded, and the Training rows line up on a phone capture. |
| 6.38 | Vignette broadcast atmosphere, in the director's words 'it looks bizarre how there are no background players or atmospheric details': the centre bounce (StoppageVignette) needs both teams' 6-6-6 set-ups, the other field umpires, boundary umpires on the wings and goal umpires; cheer squads, banners and a lit club-colour crowd beyond VignetteCrowd and #996; distant players as cheap sprites. After: 6.42, the row 31 phone frame time and the director's animation calls (section H). | Match scene captures show the extra people and atmosphere with no frame-rate drop on a phone, and the director has looked. |
| 6.40 | Written inventory of every vignette renderer (Broadcast, AwardWinner, Stoppage, Decision, Farewell, PreMatch and the Vignette* helpers) and fallback (such as OLD_FRONT_DURATION and the average-build fallback in _figure) ('entirely replace the old vignette art style with the new pre-rendered 2.5D footballer style'). | The inventory doc exists and confirms no old-style figure path is left. |
| 6.42 | Rendered Blender plates for the press room, awards stage and MCG with crowd, replacing the painted stands ('do what you think is best, but I expect beautiful results'). | Each plate is in the game in its scene and the director has looked at captures. |
| 6.44 | Ground looks beyond the MCG so 'a footy fan recognises the MCG, Marvel, Optus, Adelaide Oval, the Gabba, GMHBA and the SCG without the name' (#967). Left: his look at the no-name captures of the six, and the fictional clubs' grounds: each plays at a real regional ground near its town, e.g. Bellerive or Manuka (director 2026-11-10), a new ground look per club. After: nothing; the fictional grounds are built in row 152. | He has looked and recognises the six, and his ruling on the fictional grounds is recorded. |
| 6.49 | Oval-broadcast bundle 2 (P-31, P-32, P-33; P-34 is in T3.R10; P-35 skipped): breeze end shown, crowd, and a skippable post-full-time goals replay from the event log. After: V6. | All three show in a played match and the replay skips with one tap, proven with a real tap. |
| 6.53 | Free shader polish and lighting: restrained figure shadow and highlight in figure.gdshader, soft contact shadows, baked lighting on the figures first (rule 53). #996 did the grade and atmos pass only. Idle and battery numbers in Z | Before and after captures stored and reported. |
| 6.58 | Hair library: all 16 styles draw (#998, on), but about ten short styles (buzz, crew, side part, messy medium, curly, afro) look alike at figure scale; beards and boots go back to the art work. After: the director's answer on the hair, beard and boot ids (section H) and 6.63. | Each style reads apart at figure scale and the director has approved the look. |
| 6.63 | Tattoos: premiership-year ink is done (#1258). Left: the original tattoo library (bible item 63: rose, snake, barbed wire, bird, 666, love heart, Southern Cross stars, checked Asian-script lettering) drawn from the per-player Appearance field; ink on the speccy strips, carrier_near, the umpire's bounce and the coach; correct arm on mirrored moves; years readable at match size; his look at the ink. After: 6.38 and 6.53. | Tattoos draw on figures, are saved once, change no match result, and he has looked. |
| 6.64 | Club Forge appearance options still hidden or missing: socks, headbands, bandaging, Forge-chosen tattoos and facial hair (hidden by SHOW_UNDRAWN_LOOKS until figures draw them), boots and boot colour, beard colour; and Forge import/export as a 256x128 PNG. Skin tone, hair, foot, number and nickname are built. After: 6.58. | Each option is drawn on the figures and saved, and a PNG round-trips through import and export. |
| T7.R87 | Pass-2 bundles the director said yes to ("All eight theme bundles: yes"), Tier A and B in listed order. P-12 (oval answers a structural call, #784 and #800) and P-70 and P-71 (offline promise, backup, #779) are built. Still to build: P-25 to P-29 match day on a phone, P-72 patch notes name the football change, P-73 answer every review within a week, P-74 the Not in this game page and P-43 (P-52 carnival built in #969). After: the P-43 press slice needs nothing; the rest after V6, T7.R84 and 6.49, and P-74 from the design bible's "What this game will not have" (his list, 2026-11-12). | One row per remaining P-number with a PR, each proved on a phone-width capture or a test; P-30 and P-75 stay skipped. |
| T8.Q20 | Make the weekly sim faster. Director: "#888 sim 35% slower is accepted for now; optimise the weekly AI in a later PR (next task = the sim-speed PR); the coach pool of 57 is fine as is." Win back the lost time in the weekly AI work, with the same results. After: T1.R26's L3 and FA slices, so the seeded results stay byte-identical. | 3-season bench of weeks is back near main's pre-#888 146 s (from 225 s); seeded results byte-identical before and after; coach pool stays at 57. |
| T8.78 | P-78: a time budget for each player action (tap to screen, Sim the week, rollover), checked by a test. Director: "Yes" (Q8, audits that protect the fun, 2026-10-18); "Build it now" (2026-11-10, over T7.O19 "not now"), after T8.Q20 and 128. After: T8.Q20 and 128. | One budget table in a data file, a check that fails when an action runs over its budget, and the first baseline run recorded. |

## V. Visual direction (rulings 2026-11-04)

The director's visual rulings V-R1 to V-R9 are in Rulings (director, 2026-11-04).

| Id | What | Done looks like |
|---|---|---|
| V2 | Premiership streamers in club colours | plays once on the premiership screen only, a capture frame shows both club colours |
| V3 | Brownlow winner reveal: 24 gold sparkles After: V2. | plays once on the winner reveal only, 24 sparkles, a capture frame |
| V5 | Training results is the proof screen for the new look, then the hub, then the other screens After: V4, 135 and 6.34. | director approves Training results on his phone before the hub starts, then the hub before the rest |
| V6 | Match chrome: scorebug 56 to 72 px, bottom decision sheet about a third of the height, one-button transport, goal and siren poster card After: 132. | captures at 390x844, the oval gets the freed height, every decision reachable with a real tap |
| V7 | Navigation icon set (AI-assisted candidates) | one icon per hub destination, director approves or rejects |
| V8 | Refresh captures of every screen on current main (the newest are 2026-10-07 to 10-11) After: T3.R9 and copy passes 131 to 140. | one capture per screen at 390x844, dated, in the audit folder |
| V9 | Housekeeping: placeholder logo name, stale worktrees (`The MCG.glb` is already out of the repo) | logo name is final or marked placeholder in one place, `git worktree list` shows only live ones |

## Rulings (director, 2026-11-04)

Settled answers that are not build rows. The bible stays as it is unless he consents to a change.

- A TODO row is authorisation to build it; a roadmap entry alone is not. With no task, work the TODO.
- Any doubt is a fail; every visual goes to him after the session's own frame check (no critic agents since 2026-11-05).
- Game, simulation and story carry equal importance. Secondary buttons are outlines.
- Press answers are seeded rolls with the odds and both outcomes shown (the bible line stands; already shipped).
- Polish goal 1 (player agency in matchups and rotation changes) stays open as written.
- Teaching is XP scaling, not the season-ceiling point.
- Personality types and captaincy: wanted, later (section F).
- Row 13: all five scenes, waits for the 1.11 playtest gate; time pauses at a decision.
- Weather has full effect on play; wet tackles toward the real +12% (row 61); its look never touches the sim.
- Ladder lives in Season stats; the hub nav bar has no Ladder.
- Free for now: web, Windows and Android APK on itch; Google Play only on his written yes.
- Visual direction (section V; style guide updated to match V-R1 to V-R4):
  - V-R1 CLAUDE.md governs over the style guide: gradients and glows are allowed when deliberate.
  - V-R2 The primary button may be filled with club colour. A red club may clash with BAD, so a contrast and collision check is required.
  - V-R3 Navigation icons and relaxed motion (sliding sheets, count-ups, screen transitions) are allowed.
  - V-R4 ARD Regular stays for small body text; no Barlow A/B.
  - V-R5 Particles only for the premiership (club-colour streamers) and the Brownlow winner reveal (24 gold sparkles).
  - V-R6 The live match stays a refined diagram; the vignettes are the showpiece. No following camera, no 3D restart plan, no Clay Oval proof now.
  - V-R7 Lowest supported phone: a recent mid-range, about 2023.
  - V-R8 Figure sheets and the eight vignette scenes are kept; any deletion waits for a future decision.
  - V-R9 Nav icons and the wordmark are AI-assisted candidates; the director approves or rejects.
- Draft AI key-forward spread (2026-11-05): "Leave it as is". Young talls keep their potential credit; no change.
- Draft AI veterans (2026-11-05): "petracca and stewart should be 125-150"; Petracca overridden to 87; building clubs count a retired season at 0.35.

## Rulings (director, 2026-11-06)

- GitHub deletes a PR's branch when it merges (T7.O20; turned on 2026-11-06).
- League balance and calibration suites run nightly only (T7.O14); balance-threshold checks leave the nightly (2026-11-10).
- Phone performance budgets and a CI perf gate: not now (T7.O19).
- Tests: "do a small amount on my pc the rest github": CI on GitHub, local runs small. No self-hosted runner.
- Trade value keeps counting 60% of unproven growth (T8.Q13).
- The visual sim reacting to coaching goes before the Season stats patch (T9.Q7).
- Skills travel with the player: "their skills dont change based on position" (T9.Q27). Tap v mobile rucks, swingmen, tall v small defenders and unicorns stay deferred.
- Playtest gate 1.12 "Can I feel my decisions?" is adopted (T9.Q28).
- No single first among the audit's biggest gaps: "all are important no focus on anything particular" (T9.Q30).
- Cascadeur Indie: written yes to buy (6.Q20); show him the price, he buys it.
- Kept as they are: Club Forge create a player, the Coaching screen (T1.Q7).
- 1.x is not frozen (T7.O4). AFLW later; Google Play much later; two-screen Team selection later (T3.R41).
- The game deliberately has no paid extras, no ads and no direct player control on the field (T5.Q21).

## Rulings (director, 2026-11-10)

- Audits and balance come last, after every other row: "we can rigorously audit and balance after the game is fully featured" (section Z).
- A build row whose done-test contains an audit closes when the build ships; the audit moves to section Z as its own row ("Yes, split them").
- Balance-threshold test checks move out of the nightly.
- Career story: player sheet and Brownlow night, up to five sentences, nothing when there is no story, one plain senior-coach register (a failed pick told plainly, no warmer farewell); built in #1334 (rows 144, 145).
- Compact player cards (Team builder, Training, Off-season) show the top three attributes: "Yes, add them" (row 1).
- Row 14's goal-run moves stand (Stack the centre bounce, Flood behind the ball). Row 15's late centre ball-up changes to Flood behind the ball and Push numbers forward.
- Your own goals in the feed show in your club's colour, not blue (D6 Q74).
- The board's middle season goal is 12th or better at 18 clubs, worded "Stay out of the bottom six", never "outside the bottom third" (T9.Q20).
- The save keeps the impact ledger's coach rows per match: "Yes, keep them" (research question 5, row 144).
- Row 128, the VFL state league: "Build it".
- The transparency gate order (T7.R89): "you decide"; the order is in row T1.R26.
- Fictional and expansion clubs play at a real regional ground near their town, e.g. Bellerive or Manuka (Q51, row 6.44).
- Row T8.78, the time-budget test: "Build it now"; it overrides T7.O19 "CI perf gate: not now".
- Retire the no-digit checks off the decision gates, and check the stats columns only for clipped text, not exact pixels (T7.O15).
- Coleman cap: the 99.5th percentile (row 30).

## Rulings (director, 2026-11-11)

- The coaching-style press interview comes before the draft ("its meant to go before the draft"), in every start mode; Continue returns to the draft board (row 141).

- Concussion: "if a player gets 5 or more concussions within a 5 year period, they should have to pass a medical retirement check". The check is "Flat odds each time"; the panel sits "Straight after the fifth", so a fail ends the career that week (row 154).
- Stretch goal, not assigned: "smart phone/social media hub including contacts, a folder for players screenshots, perhaps a home for stats and news too" (row 153, section F).

- Stretch goal, not assigned: Club Opinion, each rival club's opinion of the coach, separate from the Board (row 155, section F).

- Concussion medical retirements stay rare: "maybe 0.25 per year or less", above zero, measured over many seasons.

- State league (row 128): "just make sure the state league results are simulated very fast": every match but the coach's own uses a quick result model, under 5% added to Sim the week. Coaching in the state league flips it: the AFL becomes the quick background.

- Legacy mode from 1990 is in Build now (row 142).

## Rulings (director, 2026-11-12)

- His 1.0.15 reports: section headings take a sand ink, e8cf9c ("Sand (B)"); Defensive Press is renamed High Press ("Rename High Press"; same plan, old saves map); rows 172 and 173.
- Visual overhaul: match day first, one look sheet per area, rig and Tripo without asking (rows 166-171; answers in the Director Bible). Trades check: "Decline the letter in the test".
- Auto-pick keeps its name ("I already answered this question"), exempt from the engine-word ban (row 134).
- Every draftee in every draft shows one line "Plays like: <real AFL player>", from facts: same position, about his level ("level must be included"), similar height, closest ratings at max potential (`PlaysLike.gd`). A line under the name, never in it.
- Sim speed "Speed up the engine", drift inside AFL bands (row 159). Weather "Yes, at a break" (160). Feed colours: our goals in our colour, red conceded, grey the rest, no blue (161). Pre-match calls stay pre-bounce. Vignettes on every card (162). Autopilot to mid-table (163). Draft "Must make room" (164).
- Design bible updated with his consent: the press risk line, pillars (story, deep simulator, agency, readability), a story question first in the feature test, and "What this game will not have" (all but 14 and 15).
- Merge queue on. Legacy money "Dollars of the time"; 1990-2012 cap gaps "look harder" (row 142). Press-room coach "Re-render sharper".
- Game-plan traits are removed and replaced by a custom game plan: 1 strength and 1 cost from a list, a plan of its own, neutral like Win Contest (never counters or is countered), every club can run one (rows 158 and Custom plan).
- Real names only: "remove 'generated names' from the game, Real Names only". The Player names choice is gone; row 56 has no fictional-names fallback (bible 3.35a).
- Form on team selection: "Reserves games". A weekly reserves rating shows for players in the reserves, display only, no sim effect.

## Current focus (moved from the bible, 2026-11-06)

Polish is the gap. There are two big tickets, and one priority above both.

**The single biggest improvement to game feel:** players in the visual sim really react to your coaching moves.

1. **Player agency fine-tuning.** In-match decisions and in-match and pre-game coaching moves, such as matchups and rotation changes. Each decision should feel like it has a real in-match impact and be easily measurable.
2. **Visual polish.** It should not look like an app. It should feel clean and crisp like a great app does, but also personal, like a hand-crafted game.

## H. Needs his call (questions still open, one at a time)

Each line is a question he has not answered yet. Answered ones are in Rulings or in section A.

- Are the hair, beard and boot ids final, and what happens to the 24-style hair, 10-beard and boot contact sheets he has not looked at? (6.Q4)
- His calls on the open animation decisions including the gather-on-the-run proof (Cascadeur spend is a yes)? (6.Q20)
- Which rows make up 1.1 ("tune and polish"): his looks on pre-season, draft night and the oval ring, and which Tier A items? (T7.O5)
- Which of P-01 to P-11, P-16, P-19, P-21, P-22 and P-24 does he take? (T9.Q31)

## Z. Last: audits and balance (after every other row is done)

Director 2026-11-10 (Rulings 2026-11-10): no audit or balance tune until every other row is done. Each row names the build row it came from.

| Id | What | Done looks like |
|---|---|---|
| 28 | How-we-play maturity; How-we-win materiality; List Profile vs results (seeded, via audit.yml) After: T2.25, T1.R26 and Custom plan. | a seeded audit and evidence doc for each |
| Z67 | Management pays audit, after row 67's trade lever: re-run tools/audit/levers2_impl.gd with the trade period at real volume, recruiters' edge and development projects; balance-gated After: T1.R26. | audit across 8-10 seasons, paired `tools/balance.sh match 1000` table in the PR |
| 11, T2.29 | Spoils, intercept marks and ground-ball gets (M3-003). Spoils 22.8-23.2 a team against real 30.7, between the arcs 4.6-5.1 against 14.5-20.2 (#1199, #1241; forward 50 spoils are done). Intercept marks (0.76) and ground-ball gets (0.71) not re-measured since #897; the harness needs an intercept-marks stat and a real ground-ball-gets reference first After: the T2.25 lanes audit. | a tune that keeps contested marks, rebound 50s and disposals in range, and a seeded screen shows spoils, intercept marks and ground-ball gets IN |
| T2.31 | Ruck integrity (M1-002): write the audit doc from the harness Rucks section (#1121): the number-one ruck's to-advantage 35.2% against 29.6% (NEAR), hit-outs per ruck contest 55.2% against 42.5% (OUT, a counting artifact per #1121); find a real duel-spread reference or his acceptance of the club-spread proxy; state tune or no tune. Clearances stay random After: 11/T2.29 (both edit MatchSim.gd) and the director's answer on the club-spread proxy. | audit doc with real ranges, the duel spread and the stated diagnosis; any tune follows it |
| T2.25 | Paired-seed kick lanes audit, after row T2.25 ships | lanes recorded per kick differ by plan on paired seeds |
| 6.53 | Idle and battery numbers for the lighting change (#996) and the row 6.53 shader work | idle and battery numbers reported, before and after |
| Synergy | Synergy numbers up (director 2026-11-10: "if anything i wanna boost synergy numbers but thats for later"). The row 103 audit had 47% of rival clubs fielding a synergy on main, 57% with row 103. Supersedes DIRECTOR_BIBLE ruling 23 (15-25% of clubs, mostly 0-1). Target: "i think teams at the bottom of the ladder should have 0-1 synergies, teams in the top 4 probably have 2-4 synergies" After: the row 103 playtest. | a seeded audit of synergies per club by ladder position: bottom clubs 0-1, top 4 at 2-4 |
| T8.87 | P-79: no plan wins everywhere. Seeded round-robin of every plan against weak, even and strong lists. Director: "Yes" (Q8, 2026-10-18). Reports only. After: T2.25, T1.R26 and Custom plan. | A shared-seed audit run on CI, with a result written into the term sheet in football words and the share of opponents the best plan beats; no tuning made. |
| T8.88 | P-80: fun floor beside the realism floor. A dynasty bot plays 20 seasons on many seeds and records how often it makes finals within five seasons and wins a flag within fifteen. Director: "Yes" (Q8, 2026-10-18). Feeds the dial sizes, never declares balance done. After: Balance. | A CI audit and an evidence doc giving the finals-in-five and flag-in-fifteen rates against the director's 'a flag every 8-10 seasons'; no constants changed. |
| T8.83 | Long-career integrity soak. Director: "Test decades-long / 100+ year careers." Start with 5, 10 and 20-year careers, then 8 careers x 20 seasons x 4 policies. The old long_career audit only measures lists and retirements. After: 144, T7.R84 and 128. One batch for every multi-season measure (director 2026-11-11: "make a list of things which require multi season tests, then test them all at the same time at a later time once we have more than 1 thing to test"); each new one is added here, not run on its own. On the list: (a) the autopilot career stops rolling over after 4 to 8 seasons with "off-season N did not complete" (found 2026-11-11 by rows 154 and T1.R26 L3; fix first, every other measure needs it); (b) row 154 concussion medical retirements, target above zero and at or under 0.25 a league season (tools/audit/medical_panel_impl.gd). | CI run shows zero integrity violations (duplicate history, ghost players, impossible lists), season-20 save under 3x season-2, round time under 1.5x. |
| T8.50 | Potential inflation: show how many 90+ ceilings there are by age, role and club, and what long careers do with them. No blanket nerf. The existing audit covers age band, position and source only. After: Synergy. | Evidence doc with distributions by age, role, club and source plus long-career outcomes; any change goes to the director first. |
| 30 | Coleman goalkicking cap: the clamp moves from the 98th to the 99.5th percentile (director 2026-11-10, bible Q120) | a seeded screen with the Balance pass |
| 58, 39 | Difficulty dial sizes (board patience, rival recruiting) and pre-season balance sizes After: T8.88 and Balance. | sizes set from his playtest |
| 42 | Comebacks match real AFL on 9,600 matches (docs/COMEBACKS_EVIDENCE_2026-11-05.md); loosen the close-finish band (65.8% v 57.5%) or not After: Balance. | his ruling |
| Custom plan | Custom game plan strength and cost sizes (director 2026-11-12: game-plan traits removed; "1 strength, 1 cost", neutral like Win Contest, every club can run one). Each strength and each cost is screened with `tools/balance.sh match 1000` (one side running it, paired) and sized so no pairing wins or loses on the scoreboard and none counters another plan. Built 2026-11-12 (the sixth plan in How we play, named by the coach; a quarter of AI clubs build one a season; weather and drilling do not scale it, like Balanced). First screens, the side running it v Balanced, 1,000 paired matches, its margin: Sharp shooting + Slow ball -2.7, Stoppage numbers + Open at the back -0.9, Clean hands + Kicks get read -2.3, Fitness base + Injury toll +0.3, Long kicking + Loose hands -0.0; Midfield squeeze + Open on the break +7.4 at 15%, cut to 7% it is -0.7 (se 1.4). Sizes are named consts in scripts/sim/CustomPlan.gd. After: T1.R26, T2.25 and row 158. | a screen of every strength and cost with its size in football words and percentages, no pairing ahead on the scoreboard; settled only when his playtest also passes |
| Balance | Balance pass: first run every suite with `BALANCE_CHECKS=1` (64 real-AFL threshold checks wait behind tests/balance_gate.gd; misses log a `BALANCE_DEFERRED` line meanwhile) and fix or rule on each; then every balance-gated feature in section B (78, 89, 92, 103), screened together as one match (match_flow, kick_range, set_shots, key_duels, mid_intercepts, back_carries and momentum_runaway were never screened together, #1074) After: 11/T2.29, T2.31, Synergy, Traits and 30. | paired `tools/balance.sh match 1000` table; balance settled only when his playtest also passes |
