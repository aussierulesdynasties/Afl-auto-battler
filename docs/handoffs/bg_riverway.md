# Background scene: Riverway Stadium

Session local_ec4cf7fc, worktree `.claude/worktrees/quizzical-goldwasser-d42116`.

## Where the work is now

Pipeline in .claude/review/riverway_bg/. Big files: AFL3D_archive/riverway_bg/.

---

## The session's handoff file (verbatim, C-Users-DANTE-Documents-GitHub-Afl-auto-battler-claude-worktrees-quizzical-goldwasser-d42116.md)

# Handoff: bg-riverway (Riverway Stadium background scene)

### State
available (bg-riverway). Renders HELD until the Riverway builder sends a passed md5 (8ea7b8c6 withdrawn; build stopped, nothing rendered).

### Field 1-3 sails: current step
- Chrome froze on Maps; use the built-in browser (preview_start url=pano link, drag to pan; fresh nav = black, so use preview_start per pano). Close tabs.
- Street View (Sept 2022) shows 4-corner twisted sails on white posts in the grass islands; each spans a double parking row. Field 1 splits in sails.json are guessed = FAIL.
- Photos + camera poses: proto/data/riverway/photos/sails/ (15 jpg, cameras*.json). F1: H3F3 (-496,60), Tq8J (-552,73). F2: 5Vln (-391,256), UPcY (-374,209). F3: 4O5l (-750,200), 4mnA (-760,159). Two positions per field done. F3 posts sit on concrete walkway strips and bay lines, not grass.
- Next: count posts + sails per field from the panos and aerial (all 3 fields), add the counts to the numbers table, re-trace field 1 (and re-check 2 and 3) on post lines, then do the side-by-sides with pano filename + pose once the md5 arrives.

### Task
Background scene outside the outer fence of the Riverway ground model, for the lead "AFL game handoffs" (local_64d97632).
- Match the aerial and photos region by region; every mismatch is a fix.
- The READY carries a table of measured value vs model value and the model md5.
- On the director's pass: PR with "Part of row 202" on its own line, auto-merge on green.

### Where things are
- Pipeline: P = D:/Temp/claude/be4131086f5178a8/2acaba2f-ab04-4c99-b2ff-bfdb665b1686/scratchpad/proto
- Model: P/ground/riverway.glb = 6122c025. Backups: riverway_1515c7.glb, riverway_c06b8d.glb.
- Build: `"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P scene.py -- spec/riverway.json`
- Render: the same blender with `-b out/riverway/scene.blend -P render.py -- out/riverway/job_ortho.json` (output in out/riverway/ortho/top.png).
- Don't rerun prep.py: it overwrites trees.json and buildings.json. Rerun canopy_trees.py and roof_meas.py after it if you must.
- Measured layers (data/riverway/prep):
  - trees.json (canopy_trees.py)
  - buildings.json roof palette (roof_meas.py)
  - carports.json, 1 m cells (carports.py)
  - park_cells.json and deck_cells.json (mall_surf.py): failed attempt, see below
- scene.py:
  - Tree exclusion: water, buildings, roads, bridges and paint_poly.
  - Carport canopy block after `TR = TR[~_bad]`.
- spec: rw_bigroof is set to the measured [214, 201, 188], but the mall needs splitting (below).
- Check images: P/out/riverway/chk/
  - mall_cmp3.png: model vs aerial
  - tr_nw/ne/sw/se.png: aerial tiles with a metre grid, 10 m lines, labels every 50 m

### Unfinished: mall area fails against the aerial
1. Canopies are blobs. Real ones are separate square hip sails and long rectangular carport rows: fit oriented rectangles per sail.
2. The ground around the mall is near-white. Real: grey asphalt car parks.
   - Trace the car-park outlines by hand from the tr_* tiles into spec paint_poly 'parking' (the colour mask caught house yards: rejected).
3. The NW part of the mall (about x -720..-505, y 410..250) is a tan rooftop parking deck with sails on it, not white roof.
   - Split the 55,266 m² block: deck vs white roof (white roof measures [230, 220, 210]; deck [207, 192, 177]).
4. Then compare the rest of the quadrants the same way, and the river colour (olive vs the near-black aerial).

### Next
- Get Chrome research going (via the lead), trace the polygons, rebuild, and compare the ortho.
- When the final md5 arrives: match it, render the orbit and gate the frames.

### Gotchas
- Check frames only after the render prints DONE.
- Never taskkill by image name.
- Reply to every session message.

### Update 2026-11-21 (Esri ruling)
- Ruling (stadium lead): copy the Esri 2026-02-02 capture (full canopies); count and trace on it; capture date goes on the boards.
- Made: proto/wb_fetch.py and wb_crop.py; out/riverway/chk/wb_f1.png, wb_f2.png, wb_f3.png, plus zoom halves wb_f1_L.png and wb_f1_R.png.
- Seen: all 3 fields are sail grids. Neighbouring sails meet edge to edge on shared post lines.
  - Field 1 is a band 2 rows deep at its SW end, about 4 deep at its NE end, broken by aisles at about x −545 and −500.
- Next: mark every post and sail on the crops (with PIL), count them, put them in the numbers table, re-trace sails.json, and move canopies.py to shared posts.
- Builder md5 e3755e29a7725da46732ebf294b4e0e9 (commit 94438a546, 4 dugout shelters) NOT passed yet; hold renders until builder says passed. Sails source settled: Esri 2026-02-02 (builder agreed).
