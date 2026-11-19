# TIO Traeger Park exterior: ready for gate (r13)

Branch `claude/focused-curran-a2496a`. Build scripts: `tools/grounds/traeger/` (see its README).
Model: `model/traeger.blend` and `model/traeger.glb`.

## Faults fixed since r12
1. Stand south wing, built from the c06/w04 measurements:
   - the chamfered upper window;
   - the front banding, the open middle level and the parapet;
   - the front south stair over the arch;
   - the south stair tower: two landings, a canopy blade, portal posts, white steel flights and bar rails;
   - the south face door and louvres.
2. Under the deck: the slab cantilevers over a recessed charcoal wall with a door panel. The light grey wall comes forward to the arch (s 9.0-10.9, rounded head).
3. Fence:
   - The boundary fence follows the satellite ring and is open along the stand and clubroom front.
   - Low open chain-link turns in to the arch (3 mm wire, blended alpha).
   - A black bow-top runs in the south forecourt.
   - Grey vertical bars run round the stair tower.
4. Light tower heads:
   - The pole towers have a platform with a rail, a lamp rack tilted 12 degrees to the field, and the pole running on to a crossbar.
   - The lattice towers have a square lamp head and a platform.
5. The north-end stone face is replaced by the under-deck and the stand's end cheek.

## Proofs (`gate13/`)
- `boards/triptych_w04.png`: the photo, the render and an overlay from the matched w04 camera.
- `boards/triptych_aerial.png`: the photo, the render and an overlay from the aerial camera.
- `boards/render_c06.png`: the c06 view. This camera is approximate, so use it for proportions only.
- `top/top19_*.png`: the whole ground, straight down on the satellite.
  - `_half` puts the model over the photo at 50%.
  - `_lines` draws the model edges magenta and the fence cyan.
- `top/top20_*.png`: the same for the stand and clubrooms close up.
- `boards/parts.png`: the crop board per part.
- `stills/turn_0..3.png`: the turntable stills.
- `stills/stand_facade_close.png`, `stills/clubrooms_close.png`: hand-made textures with no photo pixels.
- `stills/join_stand_club.png`, `stills/join_wing_deck.png`: the join close-ups.
- `stills/*.png` also holds a still for each part.
- `film/traeger_orbit.mp4`: an orbit of the whole ground.
- `film/traeger_west.mp4`: a pass along the stand and clubrooms.

Measurement grids stay in `measure/`.

## Texture pass (Row 202 2b)
Script: `tools/grounds/traeger/paint_tex.py` (helpers in `texpaint.py`), run after texgen/texclub/texsite.
Every mark is drawn by hand at the real module sizes: no photo pixels. Colours keep each map's mean, and the geometry is unchanged, so the `gate13/top/` overlays still hold.
- Roof sheeting: 0.76 m trimdek sheets with dirt runs along the pans.
- Render and steel: 1 x 2 m joints, rain streaks from the ledges, grime at the foot.
- Concrete: 1.5 m bays. Block wall: 0.4 x 0.2 m stretcher bond, even tone.
- Seats: moulded back, seat pan and gap at 0.5 m, empty, in their real navy and white.
- Rails: paint chips. The bow-top bars get a sky highlight.
- The ground's own signs (director 2026-11-19), sponsor logos left off:
  - "Traeger Park Oval" on the navy banner (s 15.8-19.0 m);
  - "Bowden McAdam Grandstand" on the cream band (s 14.6-19.0 m);
  - "Traeger / Park Oval" on the light-pole signs;
  - "Traeger Park Oval" on the scoreboard header.
  - The TIO boxes are a sponsor, so they are left off.
- Crowd: none to remove. The model never had one, and the seats show empty.

Grey-level stddev: every map is 10 or more, lowest 10.6. Table on `tex/tex_board_2.jpg`.

Proofs (`tex/`):
- `tex_board_1.jpg` and `tex_board_2.jpg` show one row per surface: photo crop | before | game camera | close.
- The stills follow.

Checklist:
1. Hand-made, no photo pixels: yes.
2. Every map has stddev 10 or more: yes.
3. Colours true to the photo: yes, each map's mean is kept.
4. Geometry unchanged: yes.
5. Ground's own signs, no sponsor logos: yes.
6. No crowd, seats empty: yes.
7. Inside the fence only: yes.
8. Every frame self-checked: yes.

No open faults.
