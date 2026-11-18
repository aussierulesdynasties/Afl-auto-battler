# Waverley Park (1990-99 exterior): paused, not ready for gate

Paused 2026-11-18 on the director's account-switch order.

## Done
- 06fdf00c9: the lead's five faults (gap terrace, right-end colours, near shade, tower heads C/D, left upper tier).
- This WIP commit (source/gen.py, not yet rendered into the proofs or glb):
  - Ground at s 197-220 raised 0.5-0.9 m to the photo (ZGK). Measured first: the green building's roof edge was 2.5-4 px low, and the facade foot 5 px low at s 216. s 220-248 already matched within 1 px.
  - Roof gap now starts at s 252.5, not 249.4 (photo roof runs on). The roof set ends exactly on the gap bound (ssR).
  - Roof inner edge DINK set to the photo: (195,19.7),(205,21.0),(230,21.2),(240,23.0),(246,23.6),(250,25.0),(253,26.0),(297.6,23.8).
  - Painted rows: in NZ = s 195-252.5, the block colours run on 10 more rows (to d 27.2) under the roof. Aisles are extended, with an end cap at 252.5 and no portals in NZ.
  - Kiosks: moved under the roof (d 33.6-35.3, 1.8 m tall), replacing boxes 2.6 m tall outside the facade. Groups re-placed to the photo: orange 172.2-173.6 and 204.2-205.5; red 205.8-214.8 and 216-219.

## Open faults (all must be fixed before READY FOR GATE)
1. Kiosk levels are not right yet. Photo read at the column line (d 35):
   - orange/red s 204-217: coloured band z 11.8-13.0, dark below
   - navy s 186-195: z 11.3-12.8
   - red s 168-172: z 10.9-12.0

   The planned fix: each kiosk gets a dark base from its floor up to the band's bottom, then a coloured box 1.2-1.5 m tall. The current WIP puts them on ZG (or 10.0), 1.8 m tall, so the s 204-219 group shows about 5-10 px too low.
2. Near-right corner not yet re-checked after the WIP: roof inner edge, painted rows and end cap at 252.5.
3. Stair at s 195-201.5: the photo shows it rising toward larger s, up to the upper level at about s 203. Ours rises toward s 195. Check this against the photo.
4. NEW GATE RULE (director, "Yes, every ground"): render the model straight down and overlay it on a straight-down satellite image (Google Maps or Esri) at the same scale and north. Roof edges, bowl edge, facade line and fence oval must sit on it all the way round. The plan shape comes only from top-down sources (satellite, OSM outlines), never the oblique photo. Not started. The current plan shape (fence.py, segs.json) came from the oblique photo, so it may need rework.

## Exact next step
Fix the kiosk levels (fault 1) in gen.py `kiosk()`. Then run the chain and do the near-right check with samp2/samp5. Then do the straight-down satellite overlay (fault 4).

## Chain (run in the scratch dir, or copy source/ there)
1. `python maketex2.py && python mktex3.py && python seattex.py && python turf.py && python mktex4.py && python gen.py`
2. `WAV_CYCLES=1 blender -b --python build2.py -- $PWD/out render`
3. `python ov2.py && python cmp.py && python proofs.py`
4. close-ups: `CLOSE="$(cat close.txt)" ... build2.py -- out close`
5. export: `... build2.py -- out export`
6. turntable: `GPU_SLOT_OWNER=waverley-2b bash C:/kt/gpu_slot.sh <godot> --path proj --windowed --script turntable.gd -- out/waverley_park.glb out/tt 4 22`

## Files
- Proofs (from 06fdf00c9, stale against this WIP): this folder's *.png, plus waverley_park.glb.
- Scripts: source/ (gen.py is the model; pj.py holds the projection). Measuring helpers:
  - samp2.py: roof-plane d markers
  - samp4.py: ground markers
  - samp5.py: arbitrary (s,d,dz) markers, photo over render
- Scratch (may be wiped): C:/Users/DANTE/AppData/Local/Temp/claude/5d32353bc27448d9/a374c8a7-35c6-43fd-bd2c-71da737a0440/scratchpad/wav2/ (gen_pre_nz.py = gen.py before this WIP).
- Reference photo: source/ref.jpg (one oblique aerial, 1990s). No satellite image yet.
