# Putting a build on itch.io

**Who does what.** Sessions push the builds with butler and post the devlog. The director holds the login and the keys ("I'll run butler login"): he runs `butler login` and signs in to itch in the browser, and no session runs that login or opens `~/.keys`. If butler reports it is logged out, ask him to log in again.

**When.** Only when he says (2026-11-09): "just whenever I say". No upload, version bump or devlog without his word. Each build he calls gets the next number and its own new devlog post; a post is never retitled to cover a later build.

The page is https://aussierulesdynasties.itch.io/aussie-rules-dynasties, public since 2026-10-17. The butler target is `aussierulesdynasties/aussie-rules-dynasties:<channel>`; the old gabebartolo-spec target fails with "invalid target (bad user)". The browser ("HTML") version is threaded (director, 2026-11-10: the loading screen keeps playing while a week's matches run on threads), so it needs SharedArrayBuffer: itch's "SharedArrayBuffer support" must be ticked.

## 1. Push with butler

Three channels, one version for all. The page is free.

```bash
python3 -I tools/bump_version.py      # its own PR, merged first
tools/export_builds.sh windows android web
V="$(cat builds/version.txt)"   # <version>-<sha7>, written by the export
B=~/tools/butler/butler.exe
$B push builds/web     aussierulesdynasties/aussie-rules-dynasties:html5   --userversion "$V"
$B push builds/windows aussierulesdynasties/aussie-rules-dynasties:windows --userversion "$V"
$B push builds/android/aussie-rules-dynasties.apk aussierulesdynasties/aussie-rules-dynasties:android --userversion "$V"
$B status aussierulesdynasties/aussie-rules-dynasties
```

A channel named `windows` or `android` gets its platform tag on itch by itself. `tools/export_builds.sh` hands the Android signing key to Godot itself, so no session needs to open it. The key and its backup: docs/ITCH_BUILDS.md.

The html5 channel can also take the Web build workflow's artifact: on GitHub, Actions, "Web build" (it runs on every push to main), download `aussie-rules-dynasties-web` and unzip it once, so `index.html` is at the top next to `index.js`, `index.pck` and `index.wasm`. About 25 MB zipped, mostly the figure sheets.

**Version number.** The version comes from `project.godot` `config/version` (the menu and Settings read it, and the Android and Windows exports use it); nothing else holds a copy, and `tools/check_version.py` fails CI if one appears. The butler `--userversion` is `<version>-<sha7>` (for example `0.1.13-60a1bd4`).

**Patch notes in the game.** The version-bump PR also adds the new version's lines to `scripts/core/PatchNotes.gd` (the menu shows them once per version; the `save_release` suite fails a bump without them). Same rules as the devlog below.

A push replaces that channel's build. Testers get it on their next load, and saves from the older build keep loading. If a tester still sees the old build, ask them to hard-refresh (Ctrl+Shift+R, or on a phone close the tab and reopen the link) and check the build label on the main menu.

## 2. Post the devlog

Every upload gets one, titled `Build <version> (<sha7>): ...`: patch notes in plain football words, no PR numbers or engine terms. Posting needs no further confirmation once he has called the build.

Set the redactor layer's innerHTML and the hidden `post[body]` textarea, tick `post[published]`, then Save. The in-app browser pane works when Chrome is not connected (he signs in). Saving a post in HTML mode can leave it unpublished: after any save, curl the logged-out public /devlog list and re-tick Published where a post vanished.

## 3. The page's settings

The project already exists. These are what its Edit page should show:

- Kind of project: **HTML**, with the html5 channel marked **This file will be played in the browser**.
- Viewport dimensions: 1280 x 720 (the desktop design size). **Fullscreen button** ticked.
- **Mobile friendly** ticked, orientation **Portrait** (the phone plays portrait only; the game's first tap also puts the page fullscreen in portrait).
- "SharedArrayBuffer support" **on** (the threaded build does not start without it). "Automatically start on page load" off (itch then shows a Run game button; that tap is also what lets the browser play sound).
- Pricing "No payments". Butler can't set it; it is on the dashboard, under his login.

## 4. Testers

- Open the link, press Run game, wait for the loading bar (the first load downloads about 25 MB;
  later visits are cached).
- Saves live in the browser (IndexedDB): they survive a refresh and a closed tab, but only on the
  same browser and device, and clearing site data erases them. Private/incognito windows lose them
  when closed. Tell testers.
- Desktop: Chrome, Edge or Firefox. Phone: Android Chrome and iOS Safari (iOS needs the tester to
  tap once before sound starts, as for any web game).
- Windows shows a SmartScreen warning (the exe is unsigned): More info, Run anyway. Saves live in
  `%APPDATA%/Godot/app_userdata/Aussie Rules Dynasties`.
- Android: download the APK, allow installs from the browser, open it. Saves live inside the app
  (uninstalling erases them).

## First test on a phone

For the director, since iOS Safari and real-device speed are the two things nobody could check from a computer:

1. Open the itch page on your phone and tap Run game. Hold the phone upright first.
2. Wait for the loading bar. Note roughly how long it took on your connection.
3. Does the menu fill the screen with no page scrolling or zooming? (Pinch and double-tap should
   do nothing.)
4. Tap New career and play through to the draft, or load a career if you have one. Do taps land
   where your finger is, on every screen?
5. Play a live match: tap Ball it up, watch the oval, use a quarter-time break. Is it smooth, or
   does it stutter? Tell us the phone model if it does.
6. Is there sound after your first tap? (iOS needs that first tap; check the silent switch too.)
7. Turn the phone sideways and back. The layout should change with it and keep your place.
8. Use the phone's Back (Android gesture or browser Back). It should take you one screen back in
   the game and never leave the page. (Leaving the game from the main menu is the browser's own
   tab or home button.)
9. Save, close the tab, reopen the link: Continue should show your career. Private tabs won't.
10. Note anything cut off by the notch or the bottom bar.

Send back: phone model, browser (Chrome or Safari) and what felt wrong.

## Reporting a problem

Testers send the director four things, by whatever channel he chooses (a message, an email, a form;
nothing about how to reach him is stored in the game or the repo):

1. **Build**: the small grey line at the bottom of the main menu, for example "Build 0.1.13 (a1b2c3d)".
   Settings shows the same line as the version. It says exactly which upload they played.
2. **Device and browser**: for example "Pixel 8, Chrome" or "iPhone 14, Safari" or "Windows, Edge".
3. **What happened**: what they tapped, what they expected, what they saw. A screenshot helps.
4. **Could it be repeated?** Once, or every time.

If the screen is black or stuck, also ask for the browser console text (desktop: F12, Console).

## Known issues

- Once in testing, after resizing the window and reloading, the menu drew zoomed in. A reload fixed it
  and it did not come back in about 30 further tries (resize then reload, and rotating without a
  reload, at pixel ratios 1 and 2). If a tester sees the screen zoomed in, ask them to
  reload the page, and tell you the build label and device.

## Notes

- Anything that is not in the build is not online: there is no server, no account and no network use.
- If a tester sees a black screen, ask for the browser name and version and the browser console
  (F12) text. The game needs WebGL 2, which every current browser and phone has.
