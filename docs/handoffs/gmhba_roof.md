# Fix GMHBA Selwood Stand roof (row 202 2b)

Session local_b6baf322, worktree `.claude/worktrees/trusting-edison-c1068b`.

## Where the work is now

Work is on PR #1924 (branch claude/gmhba-jss-roof, auto-merge OFF until the lead passes it). g14 committed; the g15 plant-storey edit (north face y 26.8) is committed as WIP c209d6363. g15 model md5 6c6376cd and its boards are in .claude/review/gmhba_roof_wip/.

Left to do (g15), from the session's last message:
1. Tint the Cats wall from grey-blue to the photo's cream, about RGB (192,195,182).
2. Make the band above the Cats wall pale (exterior `wall` material facing down at z 18.3).
3. Check the wedge size and dark glazing under it against f08 and Street View h90; the 0-3.5 m brick band may need to become dark glass.
4. Look at the foot of the SW tower in Street View; build the red base only if it shows.
5. Build g15 with the ground plane on; render wide, north, west and plan-on-aerial boards; self-check whole then zoomed.
6. Update the README table, push, send the lead boards, md5 and table. `mksign.py` draws GMHBA white and must be brought in line with jss_sign.png before rerunning (photo has lowercase 'a').

---

## The session's handoff file (verbatim, C-Users-DANTE-Documents-GitHub-Afl-auto-battler-claude-worktrees-trusting-edison-c1068b.md)

# Handoff: row 202 step 2b, ground lead and gate (trusting-edison-c1068b, session local_6e4c78c4)

### State

- GMHBA roof: g14 pushed (61d4cfd6); g15 in progress, see roof builder's notes.
awaiting reports (no jobs running in this session).

### Task
I lead and gate the row 202 2b ground models. Gate every READY at full rigour (photo check first, md5 == newest, camera-matched side-by-sides, measured table); faults go straight to builders. Reply to every message.

### Where things are
| Item | State |
|---|---|
| GMHBA roof #1924 (local_b6baf322) | g14 pushed 61d4cfd6 md5 9c930d6f; roof MATCH. Owes g15: cats block 3 m N, Cats wall slate colour, STADIUM block light grey + glass, red tower base, peak height over parapet, ground on in renders. Auto-merge OFF (I disabled twice); on only after my pass. |
| Cazaly's west #1898 (local_c57fc1a0) | 60a128ee / md5 5bf49f2e: cameras pass (<4 px). Rejected on raised block height, white base ramp, seat bank east of bldg_w. I turned auto-merge OFF; builder re-enables after my pass. |
| GMHBA bg (local_3b7267ac) | Shadow=wall shadow, grey sky light fix; pools sunk flush (director: "floating swimming pools"); canopy re-done on new-frame sat. Owes 4 frames + pool board + whole-scene sat overlay (+-2 m). |

### Gotchas
- The app monitor can re-enable auto-merge; re-check #1898/#1899/#1896.
- Builders may write their handoff into this file (same worktree name); keep the lead section on top.

### Roof builder's notes (side session daa22f57, reports to lead local_6e4c78c4)

### State
awaiting lead (asked: wall/block colours, GE vs 2026 photos). Pushed g14 61d4cfd6 (md5 9c930d6f) to #1924; auto-merge OFF (GitHub + monitor) until lead passes g15 boards.
g15 local only (S/w/g15.glb md5 6c6376cd): plant storey north face 20.5 -> 26.8 (Esri). Review renders have a ground plane (w/rcam.py).
Open g15 items: (1) colours: GE slate wall / light block contradict f08 + SV h95/h90 Apr 2026 (cream wall, dark wedge), awaiting lead; (2) GMHBA wedge face about half the GE area in the wide view (w/c15_w.png), fault, not yet traced; (3) red tower base seen only in GE, need a Street View at the foot; (4) peaks over the Cats wall are the exterior roof, height within 3-4 px of GE; fascia tone too dark.
Exterior builder data copied to S/gm (rebuild reproduces 2a5040de). Block/wedge/plant storey live in jss_roof/build_jss.py lines ~300-335. GE tab 1639215068 still open.
### Task
GMHBA JSS roof PR #1924 (supersedes #1899): frame fit done and PASSED by lead; then STANDS/VOID table (re-check old XY faults in new frame), then 3 clear photos per part with MATCH/FAIL side-by-sides. No rebuild without lead OK.

### Where things are
- PR worktree scratchpad/prwt, branch grounds/gmhba-jss-roof; commit f4ee67508 (geo origin in jss_roof/measured.md) pushed to claude/gmhba-jss-roof = PR #1924.
- gmhba.glb md5 b68541441d07655ce15d598e1c1d841c (unchanged).
- New origin: model (0,0) = lat -38.1579976, lon 144.3546774, no rotation; = old lat0 frame + (8.79, 24.64) m. Shift-only fit, 7 GE wall-foot pts, rms 0.51 (wb/shiftfit.json, wb/picks.csv, w/fit3.py).
- Board td_newframe.png copied to local_64d97632 notes as gmhba_newframe_topdown_b6854144.png.

### Gotchas
- GE top-down hides wall feet under overhang: pick at tilt 65 facing the wall, 2 px steps; hover readout via zoom [1040,560,1280,585].
- wallbase.json lacks the SW outer wall and the W face (use x=-120); wbcrop_ng output is 2x ppm.
- Esri W/S pave corners are under roofs or in plain sand: not pickable.
- Keep the fit tight; director wants logical fixes, not precision chases.
