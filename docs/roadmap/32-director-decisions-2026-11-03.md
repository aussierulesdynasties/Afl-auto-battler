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

## Approved cuts

- Draft pool filters (CUT_AUDIT row 9): the pool keeps position, sort and search. Club, career stage, style, trait, available-only and the Combine sort are gone, live with no switch; the pool always shows available players. Combine results stay on a prospect's sheet. No save migration needed (view state, never saved).
| 7 | Row 37 AI draft buff: on or off? | off | `ai_draft_buff` ships off (#862); it is rivals only, so the user's Pick for me is unchanged. Whether the buff should also change Pick for me is not yet decided |
| 8 | Cut "Play to Grand Final" and the long-press play-ahead menu? | cut (CUT_AUDIT row 11) | Sim the week is the only fast path: one round at a time, finals included; UI-only, nothing saved, so no save migration |
| 9 | Milestone games: switch on or off? | live, no off switch | the `milestone_games` switch is removed (Features.KNOWN, Milestones.FEATURE); the Hub milestone card, news preview and full-time line always show; recording was already always on |

## Cuts shipped

- Cut audit §10 row 1 (CUT_AUDIT_2026-11-03.md): the intra-club match (week 5) and the practice match (week 7) are one
  pre-season match, the practice match at the end of week 7, live with no switch. It keeps the stood out / struggled
  reads, the side picked on Selection, the prospect looks (tune `seen_uncertainty`, `guest_spare_number`), XP and
  injuries. Trial spots the coach leaves empty are filled by his recruiters' top picks (PracticeFill button, and
  automatically on sim / press on). Old saves drop the `intra` key and press on to week 7. The "sides of one club"
  kits (GameDB, PitchView, UiKit) went with it.
