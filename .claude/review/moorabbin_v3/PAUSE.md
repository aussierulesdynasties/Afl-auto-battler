# Moorabbin Oval (St Kilda 1990-92): paused 2026-11-18 ~22:55 AEDT, not ready for gate

## Done
- Stands, Huggins, pavilion, towers, roofs as in v3 (commit 70543c1aa).
- Gates: NE gate 9.0 m (dark break in the aerial), race gate 3.8 m (1993 panorama). Board bays 5.9 m (1993 panorama).
- Terraces: concrete steps round the banks, 20 risers over the 3 m bank, tread fitted to each sector's measured bank
  depth (23-41 m), so the step pattern differs round the ground; 1.8 m walkway at the crest; 8 low steps in the
  stand pocket. Source: 1993 panorama (steps, walkway, chain fence, grass behind).
- Crest chain-wire fence (1.2 m, posts every 2.5 m or less), split where buildings stand.
- Blank billboards on the SE and N bank tops (no lettering), ends read off the 1993 panorama, about 3 degrees accuracy.
- Scoreboard: real shape (aerial plus the 1993 panorama's back view), on the back slope, with a blank face, end posts,
  battens and rails behind.
- Outbuildings: red-roof shed, shed north and red tower dropped (outside the outer fence). White block and sawtooth
  kept (inside the ground, joined to the Huggins and the stand).
- South stand corner fixed in the latest build: steps, crest fence and the PM billboard now meet the stand's end wall
  (zoom_crest_fence_meets_stand_south.png, zoom_billboard_meets_stand.png, zoom_bank_meets_stand_south.png).

## Faults still open
1. Crest fence run between the pavilion and the sawtooth (104.4 to 107.4 degrees): not seen in any close-up yet. The low
   camera is buried in a wall; the top-down shot shows no fence in the gap. Find which object covers it and fix the run.
2. The north end of the banks (139.5 degrees): check the wedge where the steps meet the stand.
3. Parts board, turntable.mp4 and turn_*.png are from the 22:36 build, before the south-corner fix; re-run the full chain.
4. NEW GATE RULE not yet met: the plan shape must come only from straight-down sources (satellite, OSM outlines); the proof
   needs a straight-down render overlaid on a straight-down satellite image at the same scale and north. The current plan
   was fitted partly from oblique photos (panorama, aerials): redo the outline check top-down and fix anything off.
5. Bank height: the panorama suggests about 5 m (uncertain); the model keeps 3 m. Recheck with the top-down rule.
6. Unplaced possible fence breaks in the panorama at x 327-340 and 355-368.

## Exact next step
Fault 1: in scratch moor/, render a 20 m-high top-down shot over (-27.7, 100.9) with lens 18, find the object over the
104-107 degree run, fix, then the full chain (command in the handoff), then fault 4 (satellite overlay).

## Proof files
`.claude/review/moorabbin_v3/proof/` (close-ups and zooms, parts_board.png, overlay_full.png, turn_*.png),
`turntable.mp4`, `moorabbin3.glb` (latest build, south fix included).

## Scripts
Copied to `src/`: build3.py (model), build.json, fencepts.json, board3.py, shots.py, shots.json, turntable.gd,
tex_chain.py, chk/*.py (mkshots, sheet, runs, dumpv, ringover, panoring, sbpos, ends). Working copy:
`C:/Users/DANTE/AppData/Local/Temp/claude/9f4017b9c485d8cb/fb8d066d-4ddf-4085-adc6-c6288b802d1c/scratchpad/moor/`.
Textures (hand-made, procedural) in `textures/`.

## Reference photos (in scratch moor/dl/, not committed)
moorabbin-1993-last-game.jpg (1993 panorama: billboards, steps, scoreboard back, gates), moorabbin-oval-aerial-97.jpg,
aerial97news.jpg, moorabbin-aerial-2000.jpg (plan and scoreboard), moorabbin-old-grandstands1/3.jpg,
moorabbin-oval-4/5.jpg, moorabbin-oval-old1.jpg, old1.jpg, 200503-Moorabbin1/2.jpg.
No straight-down satellite image yet (needed for the new gate rule).
