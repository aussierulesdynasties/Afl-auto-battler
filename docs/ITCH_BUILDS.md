# Itch builds: when a new upload is worth it

Moved out of `docs/TODO.md` (2026-11-05) so it no longer loads into every session. Rows named here still live in `docs/TODO.md`.


The itch page runs the browser build of main as of the last upload (live: 1.0.14, 80ae2f7, threaded browser build with SharedArrayBuffer on). There are no feature switches (director 2026-11-06, #1074): everything merged to main goes into the next build. A build is worth uploading only when a player can see a difference: the listed rows are merged, CI is green and the web build ran. Sessions push with butler and post a short devlog in football words (docs/ITCH_UPLOAD.md). He says when (2026-11-09, which ends the 2026-11-06 standing permission): no upload, version bump or devlog without his word, and a devlog with every upload. At least three changes a player can see, or one big one.

| Build | Name | Ready when (rows and switches) | What a player sees |
|---|---|---|---|
| I2 | Safe to keep a career | T7.R84 save restore and frozen fixtures, T8.Q20 faster weekly sim. (Done: 57 export/import #973, T5.Q24 migration #945, T3.R56 onboarding on fresh saves #1293.) | Restore last good save, back up and move a career, no career lost on update, a quicker Sim the week, a fresh start that teaches |
| I3 | Match day on a phone | T3.R41 team selection as two screens and T3.R10 text size and colour-blind marks, both parked in TODO section F. (Done: T3.R42 one thumb #1123, 25 team builder setup before Start, 23 this week, 53 coaches' votes; 24 training grid is in the game and waits on his playtest.) | Controls in thumb reach, score and clock always visible, Larger and Largest text, no scrolling team pick |
| I4 | Look and feel | V2 to V9 merged. (Done: motion and player looks are in the game since #1074, V1, hub hero 6.Q2 #1209, app icon #1180.) | Result sheet and counts that move, the premiership streamers and the Brownlow sparkles, a hub that leads with one big thing, new faces, a real icon |
| I6 | A career with a story | `coach_arcs` and `weekly_checklist` on after his playthrough, T5.r22 sacked is not the end, T5.r23 rivals call, T5.Q25 take another club, T5.Q16 coaching hierarchy, `finals_cards_2` on. | Arcs and a weekly big call, a sacking you can come back from, offers from other clubs, finals with their own cards |
| I7 | Real grounds and crowd | 6.44 six more grounds (sizes and looks done in row 33; his look), 6.49 and 6.51 crowd and breeze. | Grounds you know from the oval alone, a crowd that follows the score |

Order is I2 first (before any build that people will save a long career in), then I3, I4, I6, I7. I1 (the new match) and I5 (off-season and the draft) shipped once the switches went on for good (#1074). A build can go early if everything it names is done. He can reorder.

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
