# TIO Traeger Park: PAUSED (2026-11-18 22:45 AEDT), not ready for gate

Paused for the account switch (the lead's order). Branch `claude/focused-curran-a2496a`.

## Done
- Model r12 is pushed (commit c72c23d). It has the field out, no lettering, no posts or nets, no boards and no east shelter, and keeps our own fence.
- Measurement of the four reopened faults is finished (numbers below). No geometry has been changed yet: `stand.py`, `model.py` and `blend.py` are as in r12.

## Faults still open (all four must be fixed before the push; director: "fix the fucking issues before pushing")
1. **Stand south wing**: wrong shape. The measured shape to build (stand frame: s along the front south->north, t back, z up; front plane t 0.6):
   - Upper volume: the 2-pane window sits in a 45-degree chamfer from (s 7.9, t 4.0) to (s 3.0, t 8.9), running from z 6.05 up to the roof soffit. Window corners (7.75, 4.15) to (6.3, 5.6), z 8.12-9.62. The south face is at s 3.0.
   - Front at t 0.6, from s -1 to 7.9, bottom to top:
     - z 0-2.7: light grey render;
     - z 2.7-3.1: cream slab band;
     - z 3.1-5.45: open middle level, with bar balustrade 3.1-4.2, white posts at s 1.25 and 4.5, a cream ceiling and a dark back wall at t 11;
     - z 5.45-6.05: cream band;
     - z 6.05-7.3: solid cream parapet.
   - Front south stair: on the walkway lane (t 0.6-1.8), rising from s 11.3 (z 2.0) to s 6.6 (z 3.1). It has a grey render upstand (top 3.25 at s 6.6 falling to 2.2 at s 10.9) and a bar rail 1 m above the treads. This replaces the gabions that showed through.
   - South stair tower:
     - L1 at z 3.1: s -4.5 to -1, t 3-18.
     - L2 at z 6.05: s -4.5 to -1, t 3-12.
     - White canopy blade: z 9.0-9.6, s -5 to -1, t 2.5-12.
     - Portal posts: s -4.5, at t 9.2 and t 11.7, up to z 12.3, with a head beam.
     - Upper flight: L2 (t 12) down to L1 (t 16.5), lane s -4.5 to -3.1.
     - Lower flight: L1 (t 18) down to the ground (t 22.6).
     - Steps are white steel, with rails with bars.
   - The south face (s -1) has grey render with a door, and black louvres further back.
   - The back canopy starts at s 3.0, not 0.
2. **Wall under the deck**: the seat-deck slab cantilevers at t 0.6 (fascia z 1.8-2.2, s 10.9-28.5) over a recessed charcoal wall (t 2.4, z 0-1.8). There is a lighter door panel at s 13.0-14.3. The light grey wall comes to the front up to s 10.9, with an arched opening at s 9.0-10.9, z 0-1.75, whose top-left corner is rounded (radius about 1.3). This replaces `plinth_front`.
3. **Fence type**:
   - Open chain-link near the stand: fmat in `model.py` must not give the backed 'rail' there; backed only in the south-west pocket.
   - A black bow-top fence (about 1.2 m) in the south forecourt.
   - A grey vertical-bar fence (about 1.8 m) round the stair tower and the south door (c08, c09).
4. **Light tower heads**: these are a flat textured quad now.
   - FL_pole needs a platform with a rail, about 8x7 round lamps on a tilted rack (about 6.6 m tall by 7 m wide), and the pole running on to a crossbar.
   - FL_2 needs a lattice tower with about 5x5 square lamps and a bottom platform.

New gate rule (director, "Yes, every ground"): the plan shape comes only from straight-down sources (satellite and OSM). The proof must include a straight-down render overlaid on a satellite image at the same scale and north, with the roof edges, the facade line and the fence oval on the photo all the way round. This is not done yet.

## Exact next step
In `tools/grounds/traeger` (or the scratchpad below):
1. Write the south wing and the under-deck in `stand.py` from the numbers above.
2. Add hand-made textures to `texgen.py`: render_grey about #a8a39a, under_wall about #55575a, door_panel, an RGBA rail_bars texture, and bow-top and vertical-bar fence textures.
3. Change the fence fmat in `model.py` and `blend.py` to the fence types above.
4. Build 3D tower heads in `blend.py`.
5. Do the full rebuild to out/r13 in the background (8-12 min).
6. Render overlays: w04 (cam_w04b, accurate), c06 (cam_c06c, approximate), aerial, plus the new straight-down satellite overlay.
7. Render close-ups of each fixed part and zooms of every join.
8. Commit, push, and report to the secretary.

## Proof and measurement files
- Measurement grids and photo crops: `.claude/review/traeger/measure/`
  - g6sw: c06 south wing grid
  - g6win: window zoom
  - g8: c08 grid
  - gw04mid: w04 front grid
  - w04_under: under-deck zoom
  - c08_sw, c09_sw, c06_full
- r12 proofs: `.claude/review/traeger/` (the boards from the earlier gate).

## Scripts
- Build: see `tools/grounds/traeger/README.md`.
- Measuring tools added this round:
  - `tri.py` (two-camera triangulation to s, t, z);
  - `prj.py` (projects s, t, z to pixels);
  - `bpp.py` (back-projects pixels onto a plane).
- Not useful: `fit06g/h/i.py` and `cam_c06c/d/e/f.json` are c06 camera refits. All are ill-conditioned (errors 30-160 px), so c06 is for proportions only. Trust `cam_w04b.json` for s and z.
- Working scratchpad (may be cleared): C:/Users/DANTE/AppData/Local/Temp/claude/4a2d69a2e2816321/2e119eb6-c1b8-4f9d-a827-983cffaeebc1/scratchpad

## Reference photos
- `tools/grounds/traeger/refs/`:
  - ref.jpg (Aug 2020 aerial);
  - web/w04.jpg (2025 front, 1280x720);
  - commons/ (c02-c09, 2025).
- t7 and w07 are pre-2020: don't use them.
