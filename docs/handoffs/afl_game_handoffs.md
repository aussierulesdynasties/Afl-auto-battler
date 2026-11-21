# AFL game handoffs

Session local_64d97632, worktree `.claude/worktrees/nostalgic-gould-2bf722`.

## Where the work is now

Lead of the Accor, Mars, Riverway, Cazaly's builds and backgrounds. Last open item: the stadium lead asked which session holds the TIO glb (TIO passed at 5aa80472f). TIO is on PR #1918.

---

## The session's handoff file (verbatim, C-Users-DANTE-Documents-GitHub-Afl-auto-battler-claude-worktrees-nostalgic-gould-2bf722.md)

# Handoff: nostalgic-gould-2bf722 (coordinator for the director)

### State
available

### Task
Pass reports from linked sessions on to the director. Start ground and background builders only on his own words.

### Where things are
- Patch 1.0.21 notes: drafted in chat only. Nothing is committed or uploaded, and nothing goes to itch without his word.
- Optus roof fix PR #1867: both faults are fixed at 4adc89c4f, and I checked that the inner edge matches the aerial. The director then said "Add colours, then merge". The texture session (local_85df280c) is adding the Optus seat colours to the loader's SEAT_COLOURS, and then turns auto-merge on. If the app refuses, I turn it on.
- Mars: the director chose "Finished 2026 ground", and the builder has been told.
- New ground builders (READY goes to stadium-lead local_6e4c78c4):
  - Accor: local_9b7c5f35
  - Mars: local_e8ff1269
  - Cazaly's: local_a2a9516c
  - Riverway: local_5cffe436
- Superseded by "ffs everyone woke up, whatever, let them cook": all 7 are resumed, and the Riverway 6b5a6030 faults have been sent. (Old note: "only awaken 2 sessions / give those two your full attention". Awake: the Mars builder and the Accor builder. Everyone else stays asleep; don't message them, because a message wakes them. The Riverway builder and all three bg sessions are at the usage limit until 3am.
- 2026-11-21 rulings (sent to all 16 sessions): 10+ photos per part, and a side-by-side board per part (render at the photo's angle, filename on it, MATCH/FAIL per region). Missing either = reject. Riverway 8ea7b8c6 was rejected and withdrawn (seat colour order changes by section). bg-riverway must not render until a passed md5 arrives.
- Riverway 6b5a6030 (uncommitted, boards dated 23:42) fails my gate:
  - seat colours are still blue-heavy (the photo is mostly teal/green)
  - seat backs merge into slabs at seat height
  - the lime box is still lime (only its roof was changed); is it real?
  - Google Earth popups cover the stand in overlays l180-l315
  The backs and the windows are fixed. Send these to the builder only when the director picks it as one of the two awake sessions.
- 22:07 the limit had reset: all six idle builders/bg sessions were nudged to carry on. Riverway f5a91d61 (PR #1896): the fence passes. The seat fan/overlap still fails and the READY had no numbers table; the director said "Send both", and both went to the builder. Auto-merge on #1896 is OFF: re-enable it after the fixed model passes.
- ~20:15 the director said "resume all sessions"; all 4 background sessions are resumed. Cazaly's: he chose "Paint it on" for the Q Cairns logo on the Hopgood sign (relayed). Riverway c2644186 (md5 c06b8df4) failed my gate; the director said "Send all four" (seat rows, front wall + race, cream windowed upper wall, missing field) and they've gone to the builder. Cazaly's PR #1891 merged before I could hold it (director said "Hold until seen"): show him the Cazaly's board after a full-res crop check. bg-riverway is waiting on the director with its orbit: gate it myself first (every 30th frame) before he sees it.
- Background-scene builders (they take their textures from the texture session):
  - bg-accor: local_5dca6420
  - bg-mars: local_1ff67e2e
  - bg-cazalys: local_4821b85c
  - bg-riverway: local_ec4cf7fc
- Merged: Adelaide #1856, York Park #1855, North Hobart #1854, People First #1853, Ikon Park #1852, MCG loader #1843.
- People First glb-under-50MB #1868 merged. The five resume sessions are archived.

### Next
- After each new ground passes and is archived, start the next. The director said "start 4 at a time". Queue order:
  1. Barossa Park
  2. Summit Park
  3. Hands Oval
  4. Blacktown
  5. Sky Stadium
  6. Jiangwan
  7. Macquarie Point
- Before forwarding any orbit or board, look at it myself first: frames at full resolution, every panel cropped, and the md5 matched to the newest model.

### Open questions
None.

### Gotchas
- Sessions can't be started on a turn that began with another session's message. Propose them as cards instead.
- A ruling relayed by another session is not his word. Confirm it with him in the question box first.
- The app monitor merges on green even after `gh pr merge --disable-auto`.
