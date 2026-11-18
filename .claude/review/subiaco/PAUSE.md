# PAUSE: Subiaco Oval exterior (row 202 step 2b), 2026-11-18 22:45 Melbourne

Not ready for gate.

## Done since 8007013cc (B redo against photo 17)
- North stand: the walkway lines were re-fitted (nslines2.json). The back seat rows sit under the white walkway, with the dark roof-shadow band. The roof no longer covers that zone.
- Aisles: north stand and lower west aisles were re-placed. They are within about 0.4 deg of the photo.
- West end: two low white buildings were built from wbld.json. B1 has a mono-pitch roof and B2 has a gable roof; neither is a plain box. The south roof's west end was slanted to the photo outline.
- Corner roof: now a grey corrugated sheet (texture 'roofcg'), matching the photo.
- WIP model: subiaco_B2_wip.glb. WIP render: subiaco_B2_wip_render.png, from the photo-17 camera.

## Faults still open (B)
1. The near-right stand facade is a blue glazed grid. Photo 17 shows a dark flat roof and about 5 tan-brown concrete slab bands. Between the bands are dark open bays, with vertical piers about every 25 px. Fix: rewrite the 'facade' texture in mktexB2.py (line ~38-44) by hand.
2. The joins have not had their final zoom check: aisles, walkways, roof edges, section edges, and the 62.3 deg east end.
3. Proofs not re-made: full-resolution overlay, parts board, 4 turntable stills, facade close-ups.
4. NEW GATE (director: "Yes, every ground"): render the model straight down and overlay it on a straight-down satellite image. Use the same scale and north. The plan shape must come from top-down sources only (satellite and OSM), never from an oblique photo. Problem to raise: B (1997) and A (1991) predate any satellite imagery we can reach; Esri Wayback starts in 2014. Ask the secretary what top-down source counts for pre-2000 eras.

## C (about 2000, photo 03)
Not started on the new standard. It needs the same work: copied exactly, textures by hand, no field, no posts and no nets. Fix every known fault and check the joins. Add the top-down overlay.
Known C faults: the roof masts are about 10 px tall at the far ends. The north-east junction is a plain white wall where the photo has a blue sign tower. The facade is a generic band, not the photo's stepped lower levels.

## Exact next step
Rewrite the 'facade' texture in mktexB2.py. Re-run mktexB2.py, rebuild buildB2.py, and compare the zoom (`zz.py renB2_k.png 700 400 880 560 5 fac`). Then check the joins, make the top-down overlay, make the proofs, and push. Then do C.

## Files
- Scratch (may be wiped): C:/Users/DANTE/AppData/Local/Temp/claude/cec579e0cf1e721a/27ab9b53-76bc-414a-b98e-5c4e22e13159/scratchpad/sub/
- Copied sources: .claude/review/subiaco_src/. This includes buildB2.py, mktexB2.py, nslines2.json, wbld.json, wbld.py, walkfit.py, ais3.py, wproj.py, send.py, zz.py, rprof.py, camB.json, layoutA.json and texB/.
- Build: `blender -b --python buildB2.py -- <abs dir> <abs out.glb> <abs ren.png>`. Add the env ZONEDUMP=1 to dump the stand points.
- Godot only via `GPU_SLOT_OWNER=subiaco bash C:/kt/gpu_slot.sh ...`.
- Earlier proofs: .claude/review/subiaco_B2_* (commit 8007013cc, which predates these fixes) and subiaco_A2_*.
- Reference photos: refs/c/01.jpg (A, 1991), refs/c/17.jpg (B, 1997 night) and refs/c/03.jpg (C, about 2000), all in scratch.
- Chrome: no tabs were opened.
