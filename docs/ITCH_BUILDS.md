# Itch builds: when a new upload is worth it

Moved out of `docs/TODO.md` (2026-11-05) so it no longer loads into every session. Rows named here still live in `docs/TODO.md`.


The itch page runs the browser build of main as of the last upload (threaded browser build with SharedArrayBuffer on; live on 2026-11-27: 1.0.21, uploaded 24 Nov). There are no feature switches (director 2026-11-06, #1074): everything merged to main goes into the next build. A build is worth uploading only when a player can see a difference: the listed rows are merged, CI is green and the web build ran. Sessions push with butler and post a short devlog in football words (docs/ITCH_UPLOAD.md). He says when (2026-11-09, which ends the 2026-11-06 standing permission): no upload, version bump or devlog without his word, and a devlog with every upload. At least three changes a player can see, or one big one.

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

## No 3D on itch until 3D 1.0 (from build 1.0.22)

The director, 2026-11-22: "i dont want to push 3D to itch until we have everything: grounds, animations,
players, presentation (camera angles etc)" (docs/3D_1_0_RELEASE.md). So the three itch presets (`Android`,
`Windows Desktop`, `Web`) carry the `no_3d` feature and leave the 3D files out: every ground model, the 3D
players, crew, heads, hair, guernsey cuts and atlases, skin and the crowd set. With `no_3d`,
`GameState.three_d_in_build()` is false: Settings offers only Tokens and Figures (no Graphics row, no 3D
grounds row), an older save's "3D oval" setting is ignored, and Club Forge's Create a player shows the name
and line with no 3D figure. The 3D scripts stay in the pack (the match screen's code names them), with the
few small textures they preload (turf blades and patches, the crew vest print, the supporters' knit
shader, about 4 MB), but nothing can open them. `tools/check_export_data.sh` exports a pack with the Android
preset's filters and features and proves all of this.

For the game with 3D on a phone, export the `Android with 3D` preset (the Android preset as it was, every ground and the 3D players; never uploaded to itch). The `Android 3D probe` preset is the phone cost-measuring app, not the game. When 3D 1.0 passes, take
`no_3d` and the 3D excludes off the three itch presets and the table below applies again.

## What each build carries, and the size budget

While the itch presets carry `no_3d` (above), this table describes a build with 3D (`Android with 3D`).

Measured 2026-11-23 (Godot 4.7.2 exports of main plus PR #2058 and this change, 33 ground models).

| Build | Carries | Size | Budget |
|---|---|---|---|
| `android` APK | the game, the 3D players (bodies, MetaHuman body and crew, moves, hair, the 11 own heads), every ground's model and seats | 913 MB (grounds 586, players 226, engine 50) | every stadium stays inside, offline (director, 2026-11-23); the hard ceiling is 4 GB, a zip's limit (a 2.6 GB test APK exported, signed and verified) |
| `windows` exe | the same as the APK | 1.0 GB exe (793 MB zipped) | under 2 GB for the one exe; past it the pack ships beside the exe (`binary_format/embed_pck=false`) |
| `html5` | the game and the 3D players; **no ground models** | 409 MB pack (398 MB before the players) | no ground models until per-ground packs: a browser holds the whole pack in memory |
| Android 3D probe | the same as the APK, plus `tools/` (the phone test scene) | 916 MB | none: a test build only |

- **Why the Web build has no grounds.** The browser loads the whole pack into memory; 409 MB is already heavy for a phone's browser, and the ground models would take it past 1 GB. A Web match plays in the plain stands every ground without a model has (`Oval3D.build`), never in a ring of seats with no stadium. Grounds come to the Web build only as per-ground packs fetched from beside `index.html` (same origin: GitHub release files send no CORS header, measured 2026-11-23).
- **The phone app carries every stadium (director, 2026-11-23).** Asked whether the phone game may use the internet to download stadiums, he chose "Keep it offline, one big APK": the offline promise (trust rule 80, P-70) stands, every stadium goes inside the APK, and every update is a full download of it. At 1.0 the stadiums with their real surroundings may reach about 2 GB (Football Park's surroundings alone are about 40 MB of glb; an estimate). The ceiling is 4 GB: an APK is a zip, and past 4 GB it would need zip64. A test APK padded to 2.6 GB (1,478 files) exported in 3 minutes, needed no zip64, and passed `apksigner verify` (v2 and v3 schemes); it was not installed on a phone. He added: "later we will try to get it smaller" (a later task: texture sizes and mesh detail per ground, both architectures or arm64 only).
- **Licences.** The MetaHuman bodies (`player_mh.glb`, `crew_mh.glb`) may ship inside the game: Epic's MetaHuman licence allows them in any engine, royalty-free under US$1M a year in revenue, never used to train AI. The 11 own heads are Tripo on a paid plan (owned). Hair: `assets/oval3d/HAIR-LICENSE.txt` (CC BY 4.0 credits and CC0). The ground models are our own.
- `tools/check_export_data.sh` exports a pack with the Android preset's filters and fails if any ground's model, the players' files or the MCG's stadium and seats are missing from it.

### Per-ground packs (built 2026-11-23)

- `tools/ground_packs/export.sh <android|windows|web> <out>` exports one pack per ground (only that ground's files: `strip.py` takes out the game files every export adds, `pack.gd` packs the rest) and `ground_packs.json`, the list a build carries at `res://ground_packs.json` (file, bytes, sha256, and `url`, where the packs are fetched from). A pack's name carries the ground folder's git tree hash, so it changes exactly when the ground does. Sizes: MCG 25 MB, Optus 37 MB, Marvel 85 MB, Engie 2 MB.
- `GroundPacks.gd` loads a ground's pack before the match builds it: from `user://grounds/` when it is on the device, otherwise fetched, checked against its size and sha256, kept, and loaded without replacing any of the build's own files. Packs a build no longer lists are deleted.
- In a match, the flat oval plays on while the ground comes (the line over it: "Downloading MCG for the 3D view: 12 of 25 MB"), then the 3D picture starts. A failed fetch says so; a tap on the line tries again. Settings has "Download every ground" in a build that fetches its grounds.
- `tools/check_ground_packs.sh [slug]` proves it end to end: a build with no ground models fetches the pack over HTTP, the next start loads the kept pack with no download, and a 3D match at the ground fails with no server, then a real tap on the line fetches it and the 3D match starts.
- **No phone build uses them:** the director kept the phone app offline (above), and CI refuses any internet permission (`tools/check_android_permissions.py`). They are there for a Web build once its packs have a host, and for a Google Play release (asset packs) if he ever wants one.

### The Web build and real stadiums (measured 2026-11-23)

`tools/perf/web_memory.sh` exports the Web build as the 3D probe with no ground models, puts the packs beside it, and plays grounds in headless Chromium (software GPU), reading the page's memory from the system:

| Step | Page process | GPU process | Godot video memory |
|---|---|---|---|
| Game started, no ground | 1,450 MB | 303 MB | |
| MCG fetched (25 MB), loaded, a match played | 1,142 MB | 941 MB | 414 MB |
| Marvel fetched (85 MB), loaded, a match played | 1,359 MB | 954 MB | 379 MB |

- **Streaming works in a browser:** both packs were fetched beside the page, loaded and built into a real stadium.
- **It cannot ship on itch's Web page as things stand.** itch's limits for an HTML game ([docs](https://itch.io/docs/creators/html5)): 500 MB extracted in all, 200 MB for any one file, 1,000 files; higher only by asking itch. The Web build's main pack is already 409 MB (398 MB on main before this work), over the 200 MB file limit by itself, so no stadium pack fits beside it. Packs would need a host outside itch that allows the page to read them (GitHub release files send no CORS header; GitHub Pages does, but holds 1 GB a site and 100 MB a file, under the ~2 GB the grounds will reach).
- **A phone's browser is the real limit.** The page needs about 1.75 GB before any stadium and 2.1 to 2.3 GB with one, measured on a software GPU (a phone's GPU memory is counted differently, so treat it as a guide). Phone browsers end tabs well below that. A desktop browser can hold it.
- **So:** the Web build can carry real stadiums on a desktop browser once the packs have a host that allows it; on a phone's browser it cannot carry a real stadium reliably, and the phone app is the way to play the 3D match on a phone. Until a host is chosen, the Web build plays in the plain stands.
