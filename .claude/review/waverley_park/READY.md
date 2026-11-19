# Waverley Park (1990-99 exterior): READY FOR GATE

Row 202 step 2b, resumed 2026-11-19 under ground_builder_rules.md. Reference: ref.jpg (one oblique aerial, 1996).

## Fixed since the pause (e76ad83b0)
- Kiosks: under the roof, levels read from the photo at the column line (coloured band on a dark base), no longer 3x too tall.
- Near-right corner s 195-252.5: roof inner edge, painted rows and end cap re-checked against the photo (samp2/samp5).
  The right-end roof edge was corrected at s 297-328.
- Stair at s 198.5-202: now rises toward larger s, with its top landing by the orange kiosk, as in the photo.
- Members stand, rear: a lower roof block at d 53-60 (z 31 down to 29), read from today's satellite. Its height is hidden
  in the photo, so it is set era-appropriately. The photo match is unchanged.
- Texture pass: every plain map is repainted by hand (paint_tex.py/texpaint.py): panel joints, rain streaks, roof ribs
  every 0.4 m, laps, soffit purlins, steel seams. The concourse is asphalt (the photo shows no slab joints).
  No photo pixels.
- No crowd: every seat shows empty in its real colour.
- North: the model is turned 4.05 deg onto true north (north.json). The glb has the oval centre at the origin, north = glTF -Z.

## Gate faults of 88c9baa78, fixed (lead's board waverley_gate_faults.jpg)
1. Near-left, along the wall s 136-170: the white concrete walkway on piers is now a dark steel deck and frame against
   the wall (steel posts at d 36 and 39.3 every 3 m, X bracing, dark rails), deck at z 10 as in the photo. The stair
   rails are dark too.
2. Apron, traced from the photo (apchk.py: photo vs render colour at traced points): plain dirt on the ring s 118-178;
   dirt slope with grass tufts s 118-182 (grass beyond d 48 for s < 160); light pink dirt in front of the green building
   s 182-187; asphalt ring s 178-252; a grey plaza s 187-200 down to d 52, with the road running on down the slope at
   s 191-199; dry grass s 200-252. Every new ground map has
   fine detail only on an 8 m repeat: no blotches, no per-patch tones, so no seams.
3. Members roof masts: tops measured from the photo at z 44.5-45.5 (median 45.0, mastchk.py), was 45.5; masts 0.3 m,
   stays 0.18 m, grey (mastg), not white.

## Proofs (this folder)
1. Camera-matched overlays: waverley_photo_render_overlay.png, waverley_overlay50_1023.png, part_*.png (six crops),
   waverley_cmp_{rf,nf,lf,mem,farR}.png (photo above, model below).
2. Turntable: waverley_turntable_0..3.png (Godot 4.7, glb as exported).
3. Facade and join close-ups: waverley_facade_closeup_{end,near,members_back}.png. Every join is clean.
4. Top-down: topdown_board.jpg (Esri today | model straight down | 50% overlay with the model outline), same scale
   (0.25 m/px) and north. Fence fit mean 0.8 m. One stretch differs: at s 355-385 today's turf edge is 2.3-2.9 m
   inside the model fence. The 1990s fence there no longer exists, and the photo fit holds, so it is left as built.
5. Textures: texture_board.jpg (hand-made texture beside a photo crop of the same surface), texture_stddev.txt.
   Every map has a grey stddev of at least 10; the lowest is aislec at 10.6.
6. Empty seats: waverley_seats_empty_near.png, waverley_seats_empty_members.png.
7. Signs: the photo shows no ground-name sign or crest on the stadium. The turf logos (ads) and ground boards are
   left out by rule. Nothing to compare.
8. No open faults.

## Model
waverley_park.glb. Scripts and the chain: source/README.md.
