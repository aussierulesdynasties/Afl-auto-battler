# Build Riverway Stadium (row 202 2b)

Session local_5cffe436, worktree `.claude/worktrees/determined-swanson-f2aa5d`.

## Where the work is now

Model merged in PR #1896; three leftover work logs copied to tools/grounds/riverway/work/.

---

## The session's handoff file (verbatim, C-Users-DANTE-Documents-GitHub-Afl-auto-battler-claude-worktrees-determined-swanson-f2aa5d.md)

## State
READY for 8ea7b8c6 (commit 1c471655) WITHDRAWN. g11.jpg shows the seat colour order changes per section, but the model uses one order for every stand section. Next: map the colours per section from ref/gi/g11, g19 and ref/more/tb_8c29, rebuild, and pull Street View/Gemini photos of the back and the dugouts (under 10 photos so far). ref/gi is untracked; commit it with the next build.
Lead rejected 8ea7b8c6. Done (uncommitted): royal block 51,81,119; dugout lime 182,178,82 (sunlit g01 samples). Still to do before the next READY:
- seat colour order per section (g11, tb_8c29; g19 adds little), then rebuild. g11: in the banner section the front rows are very pale grey-blue; in the next section the front 2 rows are mint/green with pale grey-blue mid-stand and green at the top. tb_8c29 = section C order.
- austadiums_6 (older): the dugouts look like small low lime boxes (~2 m) in front of the stand, about 3 of them; check the model's 6.5-7 m boxes against this and GE.
- 10+ photos for every part (stands, seating, dugouts, backs, roof, fence) via Street View/Gemini; counts in the table;
- a side-by-side board per part (render from the photo's camera next to the photo, filename on it), each region called MATCH/FAIL;
- seating close-up crops on the l180-l315 overlays.
Seats now: paleblue x2, mint, teal, green x2, greyblue x2 (royal block on row 6), dkgreen x2; hw 0.19.
available: rebuild b7fduur4b finished (md5 in its output tail); boards not yet gated


### Progress 2026-11-21 (after stadium-lead nudge)
- build.py: ROW_COLS now = tb_8c29 section C sampled front->back: pb,pb,mint,teal,green,gb,gb,dkg,dkg (9 rows, one green); ROYAL_ROW 5. Uncommitted, NOT rebuilt.
- Other sections differ (g11) and still need mapping; n11/g43 is front-on (7 sections), use it.
- ref/gi now 19 jpg: added g40-g48 (g40 drone back+solar roof = first real back photo; g43 front-on stand; g41/g42 seating; g44 aerial). SOURCES.txt lists the searches run.
- Counts now: seats ~21, roof ~11, dugouts ~6, back 2 (+GE). Back/dugouts short: next GE street-level captures around the back (cdp.py) + dugout check vs g43/austadiums_6.
- Chrome: never run a lazy regex over Google's 1.7 MB HTML (freezes the renderer); use indexOf scan, fire-and-forget fetch, poll. Bing/DDG from Python are useless.

### Task
Riverway Stadium, PR #1896, branch claude/determined-swanson-f2aa5d. Lead local_64d97632 gated 52810189 FAIL (6 faults). Auto-merge off.

### Where things are
tools/grounds/riverway; pipeline scratchpad/full.sh; boards .claude/review/riverway. Uncommitted edits in model/build.py, model/paint.py, work/spec.py, scripts/ui/match/Oval3D.gd.

### Done (uncommitted)
- Back: grey render (92,92,98), no streaks, no plinth bands; charcoal panels (46,60,76) 2.4x1.2 joints south of 263.0; tower pale blue-grey.
- South back: 2 doorways (y -41, -45) + high window (y -58) via onback2 in spec.py.
- Window band: strip() u is running arc length (ucum), per-side v length (no shear). Panes 1.5 m bay, 2 panes each (tb_8c29 ~1.45 m).
- Shelters real (race photo): lime (160,188,100) walls, olive roof (62,70,40).
- ROW_COLS front->back: pb x3, mint, teal, green, pb x2 (royal j6), dkgreen x2 (tb_8c29 pixel samples). Seat back taper from 0.62 m.
- Seat proof (scratchpad/seatproof.py, run with plain python): 1015 seats, closest 0.588 m, 0 overlaps.
- Google Images checked (council/convention bureau photos agree); Chrome tab closed.

### Next
1. When b7fduur4b ends: read 3a, 6, 1a-1c, t10.png whole vs photos.
2. Update 8_no_open_faults md5, commit, push, check ls-remote.
3. Send bg-riverway the md5 (told them 52810189 is stale).
4. READY to lead: full md5, numbers table (seats 1015, pane bay 1.5 m, colour samples), note that the lead misread the blue rows (pixel samples).
New GLB md5: 6b5a60308923e6c789be4cd3ded8ed5c (12,221,400 bytes)

### Progress 2026-11-21 (later)
- Pushed 94438a546, glb md5 e3755e29a7725da46732ebf294b4e0e9 (sent to bg-riverway, not gated). 4 shelters + cream roofs; topdown 4b matches satellite.
- Seat order: g43 shows same pale->teal->dark order in all 5 sections; uniform ROW_COLS kept.
- Next: 10+ photos for signage/entrance/surroundings/back/dugouts (exact counts + filenames per part, lead asked), per-part MATCH/FAIL boards, then READY to local_6e4c78c4.
