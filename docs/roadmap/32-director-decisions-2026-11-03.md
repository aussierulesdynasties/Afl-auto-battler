# Director decisions, 2026-11-03

Given in planning the story-first pass (plan: make the AFL game a story generator first). Where a later decision of
his differs, the later one wins. Nothing here edits the bible.

| # | Question | His answer | What follows |
|---|---|---|---|
| 1 | What order ranks every proposal? | 1 a fun story generator, 2 a deep and engaging simulator, 3 an easy to understand, approachable game with player agency and gamey moments | every proposal is ranked story first, then sim, then approachable |
| 2 | Is any system off limits? | nothing is sacred | any system may be cut, replaced or abandoned if the game gets better; visual work earns its place only by serving row 1's three aims |
| 3 | Whose story is it? | the coach's career (the player) | arcs centre on the coach: hot seat and sacking, being poached, a board feud, a protege rising, the veteran kept too long, the drought, legacy |
| 4 | Keep the random story deck? | keep it, and layer coach arcs on top | the 12 decks stay; multi-season arc cards are drawn alongside deck cards and remember named players and clubs (plan step 1a) |
| 5 | What comes first? | the match hero and why we won or lost | plan step 1b: each match names its hero, its turning point and one to three reasons traced to numbers in the result (MatchStory.gd, switch match_story, off until he plays it) |
| 6 | A weekly checklist? | yes: a short weekly checklist with one big arc-linked call | replaces "no weekly checklist": each Hub week shows one big call tied to an arc (drop the out-of-form star? play the kid?) plus the routine jobs; the Hub's "There is no weekly checklist" text goes (plan step 3a) |
| 7 | Row 37 AI draft buff: on or off? | off | `ai_draft_buff` ships off (#862); it is rivals only, so the user's Pick for me is unchanged. Whether the buff should also change Pick for me is not yet decided |
| 8 | Finals cards slice 2 (rows 35, 36): sizes the 2026-10-13 ruling left open? | A9 "No Grand Final talk" Standards +2; A14 "Back your players" Togetherness +2; B8 "Celebrate" costs 1 week of running off the next pre-season base | built behind switch finals_cards_2 (off) |
| 9 | B8's running cost while the preseason switch is off? | carry it silently | the debt is saved and paid into the next pre-season's running base when one opens |
| 10 | A3 "Keep the noise outside" board +1? | swap it for Standards +1 | no card of the eight rewards the board |
| 11 | Where do the Grand Final history lines come from? | only the save's own history plus data/club_premierships.csv | no line claims a final or flag the record cannot show |
