# Fremantle Oval: paused (2026-11-18), not ready for gate

## Done
- Patch 33 is in `source/build/build.py`:
  - The HQ now has nine sawtooth gables, not eight: four low, the 8.09 m one, and four tall at 5.73 m. The g34 photo shows five tall apexes.
  - After gable 9 there is a 7 m entrance section. Its ridge runs along the front and its gable end faces west.
  - Heights and widths come from the camera fits: two-storey eaves at base + 7.24 m, tall rise 2.35 m, low eaves at base + 5.38 m, low rise 1.96 m.
  - The g34 render now matches the photo's outline: `wip/proof/g34h_pair.png` (photo on top, render below).
- Photo-matched cameras:
  - `wip/fit/cam_g34h.json`: g34, error 3.0 px. Render it with `CLIPS=200` (a near-clip option added this session) so the north stand doesn't block the view.
  - `wip/fit/cam_a02s0.json`: a02, error 10.5 px.
- Patch 32 adds the `photos` render mode.
- Note: `source/build/` was git-ignored and was missing from commit 92c1441f6. It is force-added now.

## Faults still open
1. **The HQ west end is unresolved.**
   - In a02 (2020 drone), the front entrance roof is only about 5 m wide along the front (`wip/proof/wire_a02.png`, magenta = the model).
   - A higher roof apex sits about 9 m back, triangulated at about (-28.5, -97.9, 11.6) m.
   - The g34 photo is too flat-on to fix depth (`wip/proof/wire_g34.png`).
   - New gate rule: the plan shape comes only from straight-down sources (satellite and OSM). Take this section's footprint from the satellite image, then use the photos for heights only.
2. Skylights are not built yet. They are amber translucent panels on the east slopes of gables 5-7 (k 4..6), seen in a02.
3. The green pergola is not built yet. It is a row of about three small green-framed gabled bays with vines, in front of the cream west block. It shows in g34 at about x 1120-1230, y 412-428, and in a02 at about x 1200-1290, y 1635-1720.
4. The cream west block is about 1.9 m too low in g34: the photo's roof line is at y 359, the model's at y 379.
5. The purple porch sits on the west face, under the west gable, in g34. The model puts it on the front.
6. Estimates still to check against every photo that shows them:
   - the toilet roof pitch
   - the pavilion
   - the SE block
   - the media box
   - the earth bank
   - the sign sizes
7. Every join still needs a close-up check: roof edges, tier lines, section edges. Lines must meet and curves must be smooth.
8. New gate rule: render the model straight down and overlay it on a straight-down satellite image at the same scale and north. Roof edges, bowl edge, facade line and fence oval must sit on the photo all the way round.
9. Re-render the proof set (proof17.sh, renamed proof18), self-check every frame, then push and report READY FOR GATE to the secretary.

## Exact next step
Get a straight-down satellite image of the HQ (Esri or Google, with its licence noted). Fit it to the OSM footprint (way 292154259). Read the plan of the west entrance section and the high back roof off it. Then patch `hq()` and re-render both photo cameras.

## How to run (scratch tree)
The scratch working tree is `C:\Users\DANTE\AppData\Local\Temp\claude\c2bd9e4b1f2ae135\ac622a66-fdd0-4243-b129-5b81eae2a214\scratchpad\fo\`. Its build/, fit/, work/ and hunt/ folders are mirrored here in source/ and wip/.
- Render from a photo camera: `blender -b --python build/build.py -- photos out.png fit/cam_X.json 0`
- Overlay: `python work/ov.py photo render x0 y0 x1 y1 out [scale] [v]`
- Grid crop: `python work/gridcrop.py img x0 y0 x1 y1 k step out`
- Triangulate a point seen in two photos: `python fit/tri.py '{"name":{"a02":[u,v],"g34":[u,v]}}'`
- Draw the wireframe on both photos: `python fit/wire.py`

## Reference photos
Listed in `hunt/manifest.md` in the scratch tree:
- a02.jpg: 2020 drone, DJI FC2204, focal about 2770 px
- g34.jpg: 2023, from the field
- g18.jpg: 2019, from the field (camera `cam_g18.json`)
