# Itch builds: when a new upload is worth it

Moved out of `docs/TODO.md` (2026-11-05) so it no longer loads into every session. Rows named here still live in `docs/TODO.md`.


The itch page runs the browser build of main with every switch in section B off, so a build with only switched-off work shows a player nothing new. A build is worth uploading only when a player can see a difference: the switches named for it are on (he has played them), the listed rows are merged, CI is green and the web build ran. Sessions push with butler and post a short devlog in football words (docs/ITCH_UPLOAD.md). He says go; at least three changes a player can see, or one big one.

| Build | Name | Ready when (rows and switches) | What a player sees |
|---|---|---|---|
| I1 | The new match | His playtest passes `match_flow`, `ballup_two`, `goal_run_moves`, `kick_range`, `match_story`, `top_attributes`, then they go on. Rows 9, 17, 18 merged. | Play on after a won ball, two honest late ball-up choices, hero and turning point after the match, top attributes on cards, feed colours and the matchup grid |
| I2 | Safe to keep a career | T7.R84 save restore and frozen fixtures, 57 export/import, T5.Q24 migration, T8.Q20 faster weekly sim, T3.R56 onboarding on fresh saves. | Restore last good save, back up and move a career, no career lost on update, a quicker Sim the week, a fresh start that teaches |
| I3 | Match day on a phone | T3.R42 one thumb, T3.R41 team selection as two screens, T3.R10 text size and colour-blind marks. (Done: 25 team builder setup before Start, 23 this week, 53 coaches' votes; 24 training grid is behind `training_grid`, off.) | Controls in thumb reach, score and clock always visible, Larger and Largest text, no scrolling team pick |
| I4 | Look and feel | `ui_motion` on after his look (#907 and V1), V2 to V9 merged, hub hero (6.Q2), `player_looks` on, 6.36 app icon. | Result sheet and counts that move, the premiership streamers and the Brownlow sparkles, a hub that leads with one big thing, new faces, a real icon |
| I5 | Off-season and the draft | `midseason_draft` on after his playtest (row 54 built), 22 draft AI, T5.r134 inherited 2026 lists, 4.Q9 lower draftees, T5.Q23b Brownlow count, 4.Q8 McNeil. | A proper off-season, a draft that behaves, a Brownlow count to sit through, a real 2026 start |
| I6 | A career with a story | `coach_arcs` and `weekly_checklist` on after his playthrough, T5.r22 sacked is not the end, T5.r23 rivals call, T5.Q25 take another club, T5.Q16 coaching hierarchy, `finals_cards_2` on. | Arcs and a weekly big call, a sacking you can come back from, offers from other clubs, finals with their own cards |
| I7 | Real grounds and crowd | 6.44 six more grounds (sizes and looks done in row 33; his look), 6.49 and 6.51 crowd and breeze. | Grounds you know from the oval alone, a crowd that follows the score |

Order is I1 first (it is already built and only needs his playtest), I2 before any build that people will save a long career in, then I3, I4, I5, I6, I7. A build can go early if everything it names is done. He can reorder.

