# GMHBA Stadium (Kardinia Park) exterior: ready for gate

Model: `model/gmhba.glb` (built 2026-11-19 21:34 Melbourne). Stadium only: no field, posts, nets, sponsor ads,
advertising boards, banners, posters, temporary stands or crowd (seats are empty). The ground's own signs are back
(ruling of 2026-11-19). Hand-made textures only, no photo pixels.

## Faults fixed this round (gate 2)
- Seats are built as seats (p12). Every seating tier is now stepped concrete rows, about 0.8 m deep, and each row
  carries 3D seats: a pan 0.42 m up and a back tilted up to 0.88 m. The shells are hand-drawn: blue and white, a
  rolled top lip, the cup holder on the back's top corner and curved, shaded sides. They are cut out by alpha (glTF
  alpha mask), so the concrete shows between seats. The colours run in pairs, shifted one seat per row. Aisles run
  straight down each tier every 8 degrees, with yellow step nosing. The whole model is 101,691 triangles.
  Proof: row 5 of `proof/textures/texture_board.png`: p12 | `tex_seats_close.png` | `tex_seats_row_close.png`
  (from an aisle, eye 1.25 m above the step).
- Roof top: the north stand's sawtooth roof had navy striped faces (`solar`). Both faces of each fold are now the pale
  grey sheeting, as in p1. Proof: row 3 of the texture board, plus `proof/overlays/ov_p1.png` and the turntable.
- Kept as they passed: the crest, top-down, p1 overlay, both name signs, the PREMIERSHIP STAND band and no crowd.

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
tileable noise and drawn detail, with no photo pixels. Tiles are 8 m per 1024 px (128 px/m); the seat
shells are drawn in `build/seatshell.py` on a 2 m tile (4 seats, 256 px per seat).
- Concrete (wall, cream precast, recess): 2.0 x 1.6 m panels, dark joints, a tone per panel, blotching, and rain
  streaks under each ledge. The recess also has rake beams every 4 m.
- Roof sheeting (roof, roofdark, roofgrey, underside): ribs 0.25 m apart, each with a lit crest and a shadowed flank,
  dirt along the ribs, and an end lap every 4 m. The underside ribs are stronger, because p13 shows deep shadow lines.
- Seats: 3D rows (tread, riser, pan, back). The shells are alpha-cut 0.5 m seats with a 1 cm gap, rolled lip, cup
  holder and shaded sides, in four row bands. The colours follow p12: blue (20,88,150) and white in pairs, shifted
  one seat per row. The treads are concrete, with a joint every 2 m. The aisles are paler steps with yellow nosing.
- Painted steel and fascias: 0.4 m folded cladding panels with two facets, staggered joints and grime at each panel
  foot. The teal fascia uses 1.0 m panels. Steel (towers, navy, soffit) has panel seams and grime toward the bottom.
- Sizes are estimated from photos p8, p11, p12 and p13, not measured: concrete panels 2.0 x 1.6 m, cladding 0.4 m,
  ribs 0.25 m (Klip-Lok is about 0.23 m), seat rows about 0.8 m, seats 0.5 m.

No crowd (standing rule, 2026-11-19): the crowd that was painted on the seat textures is deleted from the code. The
scoreboard's painted "live crowd picture" is replaced by a blank screen, switched off. All seats show empty.
Crowd parts removed: the people painted on the `seats`, `seats_dark` and `crowd_shade` textures (62-92% of seats),
and the scoreboard screen picture. The model had no crowd cards, billboards or crowd meshes. Close-up of a seating
tier showing empty seats: `proof/textures/tex_seats_close.png`, and from seat height `tex_seats_row_close.png`
(game distance: `tex_seats_game.png`). The flat `seats`, `seats_dark`, `crowd_shade` and `seats_empty` textures are no
longer in the glb.

Stddev of every texture in the glb (grey levels 0-255; 10 or more counts as not flat):

| Texture | Stddev | Texture | Stddev | Texture | Stddev |
|---|---|---|---|---|---|
| wall | 16.4 | roof | 13.4 | seatback | 72.6 |
| cream | 17.4 | roofdark | 12.2 | seatback_d (in roof shade) | 40.0 |
| recess | 11.9 | roofgrey | 13.0 | seatpan / seatpan_d | 68.0 / 37.4 |
| fascia | 16.8 | under | 19.6 | tread / tread_d | 18.2 / 10.0 |
| teal | 10.7 | aisle / aisle_d | 20.2 / 11.1 | turf | 10.5 |
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
