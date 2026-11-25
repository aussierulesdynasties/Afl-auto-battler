# GMHBA Stadium (Kardinia Park) exterior model

The match model is `assets/grounds/gmhba/gmhba.glb`: this folder's `gmhba.glb` (below) after the post pass
(`post/`, 2026-11-22), with Kardinia Park and Geelong round it (`surrounds.py`). Both are checked against Google
Earth 3D from the same cameras (`qa/`), the MCG standard's gate (docs/MCG_STANDARD.md).

## Post pass and surrounds (MCG standard, 2026-11-22)

    python3 tools/grounds/gmhba/post/mktex.py tools/grounds/gmhba/post/tex
    python3 -c "import runpy,sys; sys.argv=['post','tools/grounds/gmhba/gmhba.glb','assets/grounds/gmhba/gmhba.glb','tools/grounds/gmhba/post/tex']; runpy.run_path('tools/grounds/gmhba/post/post.py')"
    python3 tools/grounds/gmhba/surrounds.py        # fetches four OpenStreetMap tiles

After a Godot import, put back any other ground's extracted textures the import rewrote (git checkout).

What Google Earth showed and what changed:
- The Joel Selwood Stand roof (below) had never reached matches: the game still loaded the exterior without it. It is in now.
- North stands' roof: the outer half of every folded plate carries a field of near-black solar panels (Google Earth,
  every view from the north). The gate-2 note had made both faces plain sheeting from photo p1; Google Earth's
  current imagery wins. Panels: `post/tex/solar.png`, on the `roof`/`roofg` faces 25-125 degrees round from east.
- North stands' outside wall: white fluted cladding, a white band, a dark glazed band (`fac_north.png`), with
  16 white V struts modelled in front of it (0.25 m tubes, one V between each pair of roof folds). East (Reg Hickey
  Stand, Moorabool Street): pale grey panels and three window strips (`fac_east.png`, one tile a bay), with 9 white
  pilasters modelled under the roof's 9 ribs. Both were plain `wall` concrete.
- Seats: drawn black in every match (the seat shells' alpha cut-out, glTF MASK, renders black on the Mobile
  renderer). The shells are gone: `post.py` stands 36,064 instanced 3D seats on the seatpans (one each 0.5 m, MCG
  template, `seats_seat_gmhba_{blue,white}.bin`), slate navy, pale grey in the Reg Hickey Stand (as Google Earth), and the crowd sits on them.
  `MATERIAL_FIX` takes back the darkening painted into the `_d` (under the roof) treads.
- No painted-on geometry (docs/MCG_STANDARD.md). Besides the struts, pilasters and seats: the Players Stand's
  south-west face had white slats painted on its top 71 %, now 99 modelled slats over a plain navy backing; the
  recess under the west upper tier had its rake beams painted, now 168 modelled concrete beams; the Reg Hickey
  Stand's south end was one flat wall carrying a painted picture of the building, sky included, now cut to the
  building's own stepped outline. Left painted, being flat: windows, louvres, panel joints, signs, roof ribs. Still
  painted and small: the `fins` screen (24 m2) and the `plant` grille on the south-east corner.
- Later passes, from Google Earth close-ups (`qa/detail.json`): the south-east corner was a grass yard and is a
  14-row stand of 812 pale seats with the screen at its back; the scoreboard's red casing is modelled round a plain
  screen; the four light towers carry rows of 487 modelled floodlights (were three boxes each); the `fins` screen is
  18 modelled fins over a dark backing; the Premiership Stand's Cats wall is silver-grey cladding, not cream.
- Cats emblem: the source's was a crude drawing (square-eared cat, a star for a nose). `post/trace_emblem.py`
  traces the real emblem from Google Earth's close view (flat navy, white and pale blue only; GEELONG and CATS set
  in type at the traced size) into `post/tex_src_cats_emblem.png`; `mktex.py` erases the old one and puts it where
  Google Earth has it (0.17 of the wall wide, centred 0.31 across). The screenshot itself is never committed.
- Match fit: `GroundModels.FIT` is the largest ellipse every front-row seat stands outside (the seat rule), and the
  land ring starts 4 m past it (`fence_margin`) so nothing pokes through the fence. Trees are gum crowns.
- After every `post.py` run: `godot --headless --path . --script tools/grounds/seat_check.gd -- --write gmhba`
  (the seat rule's headroom and floor fix), then `tools/run_tests.sh ground_seats`.
- Surrounds: Kardinia Park's ovals and pools, the streets, about 1,360 trees and Geelong's houses (single storey,
  hipped roofs in tile and Colorbond colours) from OpenStreetMap, as at the MCG.

Known gaps, not fixed here: the Cats sign block's position (below); a straight-down camera shows bands of light across the west
seats (no match camera looks straight down); the town fades to plain ground past 1 km (the background scene covers
the horizon); the `fins` and `plant` screens above.

## The exterior

`gmhba.glb` is the exterior that passed the gate at commit ff1fdabab (md5 2a5040de694f1afe4bf9c26f0d14db3e), with the Joel Selwood Stand (JSS) roof rebuilt on top of it (below).

- Exterior build scripts: `src/` (from .claude/review/gmhba/build at ff1fdabab; renamed from build/, which the repo .gitignore excludes).
- Exterior gate notes: `READY.md`, `proof/topdown/players_roof_bays.txt`.

## Joel Selwood Stand roof

Built from the exterior above by `jss_roof/build_jss.py` (Blender 5.2):

    blender -b --python jss_roof/build_jss.py -- <exterior 2a5040de>.glb gmhba.glb <abs path to jss_roof/>

The roof copies the Esri aerial and the Google Earth 3D view (camera solved from the four tower tops/bases and the cats sign: rms 4.43 px, max 6.27 px at 1280 wide; held-out points 11.8 and 8.4 px).
- Outer zone: low folded plates whose fold lines meet the west edge at the aerial dots; behind the block it is a flat sliver (no folds, as in the aerial).
- Zigzag step: the inner folded plates stand up along a 6-ridge zigzag, 2 ridges behind the block.
- Eave slopes from 16.4 m (south) to 14.0 m (north), measured by back-projecting the GE eave; silver-white roof, dark glass under the eave.

The textures are hand-made by `jss_roof/mktex.py`; there are no photo pixels. There is no crowd.

| Part | Measured (source) | Model |
| --- | --- | --- |
| Inner zigzag ridges | 6, 2 behind the block (aerial) | 6, 2 |
| Outer fold apexes on the west edge | y 71.6 / 57.5 / 45.3 m, then 12.2 m pitch (aerial) | same |
| Outer ridge rise | 1-2 m (GE elevation readout) | 2.0 m |
| Inner step | about 4 m (GE readout); 5.8 m from 3.5 m shadows; the wide view cannot separate them (both rms about 5 px) | 4.0 m |
| Eave height | 13.96 / 15.17 / 16.39 m at y 78 / 40 / 2.4 (GE wide back-projected; ground check -0.95 m) | 16.4 - 0.0315 (y - 2.4) |

Known, not in this roof: the cats block (from the passed exterior) sits about 3 m south of the aerial.
