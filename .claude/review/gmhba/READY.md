# GMHBA Stadium (Kardinia Park) exterior: ready for gate

Model: `model/gmhba.glb` (built 2026-11-19 20:51 Melbourne). Stadium only: no field, posts, nets, sponsor ads,
advertising boards, banners, posters, temporary stands or crowd (seats are empty). The ground's own signs are back
(ruling of 2026-11-19). Hand-made textures only, no photo pixels.

## Faults fixed this round (gate of 7cd2c798d)
- Crest: the cat face is traced from the p1 crop on a grid, each half on its own: almond eyes with pupils, the
  white star between them, the nose and mouth, wavy whiskers through the first hoop, and the chin. The rim's flared
  top corners are traced too. The trace is pre-warped to the facade's angle in p1. Proof:
  `proof/signs/crest_board.png` (photo p1 | model through the p1 camera | the hand drawing, all at the same size).
- Seats: the seats now sit tight together as in p12, blue and white with no grey gaps between seats. The new proof
  `proof/textures/tex_seats_row_close.png` is shot from seat height (1.3 m), looking across the tier along the rows.
- Navy steel, deck and soffit: each has a free-camera close-up next to the surface, shown beside a p1 crop and the
  model at the same crop (rows 7-9 of `proof/textures/texture_board.png`). The navy columns' UVs now stay inside one
  steel panel, which removes a two-tone band the close-up showed.

## Top-down (Esri z19, north up, 0.25 m/px, lean corrected y+0.035 z): model edge vs satellite
| Sector (deg from pitch centre) | Result |
|---|---|
| Players Stand roof 204-275 | every notch and tip within 0.03-1.75 m (`proof/topdown/players_roof_bays.txt`) |
| West face 168-200 | about 0.5 m |
| Low SW canopy 131-165 | about 1 m |
| West 110-130 | about 1.5 m |
| NW stair tower 99.5-105.5 | 48.75 vs 47 m (1.75 m) |
| North stand 60-100 | 49.5-50.5 vs 50-51 m (under 1 m) |
| NE corner 20-36 | 1-2 m |
| East -20..20 | 21-23 vs about 22 m (about 1 m) |
| SE roof -100..-82 | zig-zag within about 1 m |
| SE pocket 279-303 | block 45 vs 45 m; kerb within about 1 m |
| Light-tower heads | NW and SW within 2 m; SE and NE moved onto them |

## Proofs
- `proof/topdown/topdown_board.png` (outline on the satellite plus the table), `ol.png`, `top2.png` (raw ortho),
  and `unwrap_*.png` polar unwraps (6 px per degree and per metre; red is the model edge).
- `proof/overlays/ov_p1.png` and `ov_p2.png`: camera-matched renders over photos p1 and p2 (blend on top, edges on
  the photo below).
- `proof/turntable/turntable.mp4` (72 frames, 5 degrees apart, 12 fps), plus four stills.
- `proof/closeups/`: facade close-ups and six join close-ups (NE 36, NW 100, SW box 156, W/Players 209, SE pocket 278,
  E pocket 320), with `joins_sheet.png`.
- `build/`: build and proof scripts (`run.sh` rebuilds textures, model and renders).

## Texture pass (approved for all grounds, 2026-11-19)
Every big surface is painted by hand in `build/texdetail.py`, which runs after `tex.py` and `mktex.py`. It uses
tileable noise and drawn detail, with no photo pixels. Tiles are 8 m per 1024 px (128 px/m); seats use 12 m.
- Concrete (wall, cream precast, recess): 2.0 x 1.6 m panels, dark joints, a tone per panel, blotching, and rain
  streaks under each ledge. The recess also has rake beams every 4 m.
- Roof sheeting (roof, roofdark, roofgrey, underside): ribs 0.25 m apart, each with a lit crest and a shadowed flank,
  dirt along the ribs, and an end lap every 4 m. The underside ribs are stronger, because p13 shows deep shadow lines.
- Seats: 16 rows per 12 m (0.75 m rows), 0.5 m seats tight together (a dark join line between seats, no gaps), the row's shadow on the tread, and a 1.2 m aisle with
  yellow step nosing. The colours follow p12: blue (20,88,150) and white in pairs, shifted one seat per row.
- Painted steel and fascias: 0.4 m folded cladding panels with two facets, staggered joints and grime at each panel
  foot. The teal fascia uses 1.0 m panels. Steel (towers, navy, soffit) has panel seams and grime toward the bottom.
- Sizes are estimated from photos p8, p11, p12 and p13, not measured: concrete panels 2.0 x 1.6 m, cladding 0.4 m,
  ribs 0.25 m (Klip-Lok is about 0.23 m), seat rows 0.75 m, seats 0.5 m.

No crowd (standing rule, 2026-11-19): the crowd that was painted on the seat textures is deleted from the code. The
scoreboard's painted "live crowd picture" is replaced by a blank screen, switched off. All seats show empty.
Crowd parts removed: the people painted on the `seats`, `seats_dark` and `crowd_shade` textures (62-92% of seats),
and the scoreboard screen picture. The model had no crowd cards, billboards or crowd meshes. Close-up of a seating
tier showing empty seats, from seat height: `proof/textures/tex_seats_row_close.png` (from above the tier:
`tex_seats_close.png`; game distance: `tex_seats_game.png`).

Stddev of every texture in the glb (grey levels 0-255; 10 or more counts as not flat):

| Texture | Stddev | Texture | Stddev | Texture | Stddev |
|---|---|---|---|---|---|
| wall | 16.4 | roof | 13.4 | seats | 66.2 |
| cream | 17.4 | roofdark | 12.2 | seats_dark | 36.3 |
| recess | 11.9 | roofgrey | 13.0 | crowd_shade (empty seats in shade) | 36.3 |
| fascia | 16.8 | under | 19.6 | seats_empty | 66.2 |
| teal | 10.7 | solar | 28.8 | turf | 10.5 |
| tower | 11.5 | glass | 20.8 | deck | 11.1 |
| navy | 13.0 | aglass | 12.5 | deckg | 12.4 |
| soffit | 11.4 | pave | 12.0 | blueband | 15.4 |
| beige | 72.4 | wedge | 36.3 | wedgef | 31.2 |
| rhend | 70.9 | slats | 74.2 | screen | 23.5 |
| sign | 35.4 | lamp | 93.4 | plant | 64.9 |
| fins | 46.8 | | | | |

The textures `line`, `pad`, `logo`, `banners`, `photo` and `players` exist in the build but no face in the glb uses
them (field, posts and banners are off).

Proof: `proof/textures/texture_board.png` has one row per surface type: concrete, cladding, roof top, roof
underside, seats and painted steel. Each row shows a photo crop, the game-distance shot (Godot, fov 30, about 100 m)
and the close shot. The single shots are in `proof/textures/` (`tex_<surface>_{game,close}.png`), with extra rows for
roof_dark, recess, teal, precast, paving and glass. Navy steel, deck and soffit have no game-distance sightline, so
each row shows the photo p1 crop, the model through the p1 camera at the same crop, and a free-camera close-up
(`tex_steel_navy_close.png` 4 m off, `tex_deck_close.png` 3 m above, `tex_soffit_close.png` 2.5 m below).

## Signs (ruling of 2026-11-19: the ground's own signs, hand-drawn from p1)
`proof/signs/signs_board.png` shows each sign as a photo p1 crop beside the model rendered through the fitted p1
camera. Letters use the repo's Barlow fonts (SIL OFL 1.1), drawn in `build/signs.py` and `build/crest2.py`.
1. GMHBA STADIUM on the dark wedge front: sky-blue cross mark and "gmhba", white STADIUM.
2. The Geelong Cats crest on the Premiership Stand: traced by hand on a grid of p1. It has the navy band with
   GEELONG, the hooped cat face (eyes with pupils, the star between them, nose, mouth, whiskers, chin), the white
   rim with its flared top corners and dark edge, and CATS below. Pre-warped to the facade's angle in p1
   (`build/crest_warp.json`). Side by side: `proof/signs/crest_board.png`.
3. PREMIERSHIP STAND: white letters along the navy band.
4. gmhba STADIUM on the roof front: "gmhba" on the cyan panel, STADIUM on the grey.
Left off: sponsor ads, boards, banners and posters, and the lettering on the scoreboard frame (likely advertising).

## Open questions
- SE pocket: the satellite shows a light ribbed structure out to x 28-33. Photo p1 shows a low seat bank and a grey
  multi-level building. The imagery dates may differ. The model follows the satellite plan, with heights from p1.
- SE light-tower head: the direction it faces could not be read with confidence from the satellite.
- Photo p1's camera puts the west canopy about 10 m deeper than the satellite does. Heights were re-solved to keep the
  photo rows; the plan follows the satellite.
- Photo p11 shows signs on the Gate 1 glass entrance: GATE 1 POLLY FARMER, a GMHBA STADIUM wordmark and JOEL
  SELWOOD. The model has no separate Gate 1 facade, so these signs are not in. Should that entrance be modelled
  with its signs?

No open faults.
