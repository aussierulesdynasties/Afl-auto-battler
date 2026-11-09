# Itch builds: when a new upload is worth it

Moved out of `docs/TODO.md` (2026-11-05) so it no longer loads into every session. Rows named here still live in `docs/TODO.md`.


The itch page runs the browser build of main with every switch in section B off, so a build with only switched-off work shows a player nothing new. A build is worth uploading only when a player can see a difference: the switches named for it are on (he has played them), the listed rows are merged, CI is green and the web build ran. Sessions push with butler and post a short devlog in football words (docs/ITCH_UPLOAD.md). He says when (2026-11-09, which ends the 2026-11-06 standing permission): no upload, version bump or devlog without his word, and a devlog with every upload. At least three changes a player can see, or one big one.

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

## Platforms and channels (row 82)

Every upload goes to all three channels with the same `--userversion` (`<config/version>-<sha7>`). The price is free (T7.O1, T7.O3). Google Play stays off until the director's written yes.

| Channel | File | Made by |
|---|---|---|
| `html5` | `builds/web/` (index.html at the top) | the Web build workflow, or `tools/export_builds.sh web` |
| `windows` | `builds/windows/AussieRulesDynasties.exe` (64-bit, project icon, version from config/version) | `tools/export_builds.sh windows` |
| `android` | `builds/android/aussie-rules-dynasties.apk` (arm64-v8a and armeabi-v7a, release-signed) | `tools/export_builds.sh android` |

- **The Windows exe is unsigned.** Windows SmartScreen shows "unknown publisher" the first time; testers press More info, Run anyway. A code-signing certificate costs money and needs the director's written yes.
- **Android signing key.** The release keystore is `~/.keys/ard-release.keystore` (alias `ard`, RSA 2048, 10000 days, made 2026-11-06), its password in `~/.keys/ard-release.pass` beside it. Neither is in the repo or in `export_presets.cfg`: `tools/export_builds.sh` hands them to Godot through `GODOT_ANDROID_KEYSTORE_RELEASE_PATH`/`_USER`/`_PASSWORD`. **Back both files up off this machine.** Android installs an update only when it is signed with the same key: lose the keystore and every later APK must be uninstalled first, which wipes the tester's career.
- **Android SDK.** The Android export needs the SDK (platform-tools, build-tools for `apksigner`) at the path in Godot's editor settings (`export/android/android_sdk_path`), and the JDK 17 path in `export/android/java_sdk_path`. Godot 4.7.2 refuses the export without them.
- The price is set on the itch dashboard (Edit game: Pricing "No payments"); butler can't set it. The `windows` and `android` channel names give each upload its platform tag by themselves.
- `tools/export_builds.sh` refuses a tree with uncommitted changes, because the build label names HEAD; an upload is always exported from a clean commit (best: main after the version bump merged).
- **Itch only when he says (2026-11-09).** "we dont need to push to itch after every day or every update / just whenever I say / and the build needs to climb sequentially". No upload, version bump or devlog without his word. Each build he calls gets the next number, with its own new devlog post; a post is never retitled to cover a later build. Overrules any earlier rule to refresh itch unprompted or edit the last post for a follow-up build.
