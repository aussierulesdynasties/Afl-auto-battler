# Moorabbin Oval (St Kilda 1990-92) exterior v3: READY FOR GATE

Stadium only (stops at the outer fence). No field (the game draws its own), no goal nets, no crowd.

## Files
- moorabbin3.glb: the model.
- proof/turntable.mp4: 96-frame Godot turntable. proof/parts_board.png: parts board. proof/overlay_full.png.
- proof/*.png: 62 close-ups, one on every join (fence, gates, bank to stand, stand ends, pavilion, crest fence, seats, signs).
- proof/texture_sheet.png: each hand-made texture beside a crop of the real surface from the 1993 photos.
- topdown/: the straight-down model render overlaid on straight-down satellite imagery, same scale, north up.
  tdov_L.png (half-opacity fill) and tdov_R.png (outline) cover the whole ground; tdc_L.png shows the club complex;
  rr_cmp.png is the same complex rectified along the Huggins Stand; cz_both.png shows the crest posts on the 2014 and 2017 images.
- src/: build3.py, build.json, shots.json, scripts; src/chk/texstd.json holds the measured texture stddevs.

## Sources
- Plan shape comes only from straight-down imagery: Esri Wayback 2014-07 (release 3026) and 2017-02 (release 31026), z19.
  The model sits within about 1-2 m of both: fence oval, Huggins roof (15 m deep, 49.5 m long, ribs every 4.95 m),
  sawtooth slabs, rear roof, brick block, whiteblock, pavilion.
  The club buildings are assumed unchanged since 1990-92; no era straight-down image was found.
- Heights and looks come from the oblique photos (1993 panorama and moorabbin-old-grandstands1.jpg).
  Estimated heights: the brick block is about 11 m (the panorama shows it level with the pavilion). The rear roof is
  given 11 m, under the sawtooth line, because no photo shows it.
- Light towers: era-appropriate, placed from the aerials.

## Textures (all hand-made, no photo pixels; grey stddev 0-255 as used)
All are 10.5 or higher. The lowest are the Huggins roof (10.5) and the scoreboard face (10.7). Full list: src/chk/texstd.json.

## Seats FAIL on 41a2cbfd4 ("Send seats back"), closed
1. Huggins and pavilion seats read as continuous slabs at seat height. Each seat is now a moulded shell copied from the
   Huggins photo: a dished pan with a rolled front lip, and a curved back leaning 12 degrees that narrows to the top.
   The shell is 25 mm thick and sits on a pedestal. Seats are 0.44 m wide at 0.50 m pitch, so a 6 cm gap shows between
   every seat. The shells shade smooth and the pedestals stay flat.
2. The plastic was speckled. hand/plastic.png is now an even, smooth finish: flat 150 grey with only a very gentle,
   large-scale shade (grey stddev 2.5), no speckle. Plastic is exempt from the grain stretch in timg().
The long-stand benches are unchanged (they passed). The model is now 910k triangles (the seats were 346k).
Proof: proof/seats_vs_photo.png (seat-height render beside the photo crop for each stand) and proof/seat_*.png.

## Seats reopened ("Send seats back"), closed
Seats were flat painted strips. Now every stand has real 3D seats, empty, in their real colours (proof/seats_vs_photo.png:
seat-height render beside the photo crop for each stand; also proof/seat_*.png):
- Huggins: 720 blue (front tier) and 1274 green (middle and upper tiers) moulded seats. Each has a pedestal, a pan
  (0.44 x 0.40 m at 0.42 m) and a back leaning 12 degrees, at 0.50 m pitch, so there is a 6 cm gap between seats.
  The treads under them are plain concrete (the painted seat texture is gone).
- Ian Drake pavilion: 245 of the same green seats on its 7 treads. No close photo of the pavilion seats exists among the
  sources, so they copy the Huggins green seat.
- Long stand: the photo (moorabbin-old-grandstands3.jpg) shows long green timber benches, not single seats, so they are
  copied as benches: 3 seat slats and 2 back slats with real gaps, on steel brackets every 1.4 m; runs end at aisles.
- Seats are one shared seat shape copied along every row and merged into one mesh per stand (huggins_seats,
  pavilion_seats, longstand_benches). Model is now 346k triangles and 29.5 MB (was 10.5 MB).
- New hand-made textures: hand/plastic.png (fine moulded grain) and hand/timber.png (painted timber grain).

## Gate 2 (60c52dc6d) proof faults, both closed
1. park_grass crop showed legs and a fence: now a crop of the bank-top grass strip (hb/moo-3-goals.jpg).
   That crop showed the texture was too fresh a green, while the bank grass is olive (photo mean RGB 110,102,31;
   the sky in the same photo is true blue, so this is not a film cast). Texture recoloured to that mean, grain kept.
2. steel crop was a sliver: now three crops (galvanised post from hb/moo-5-keep-off.jpg; light tower pole and head
   from dl/200503-Moorabbin2.jpg). Those crops showed plain grey steel, while the texture had a rust gradient that
   banded the light-tower poles orange every metre. The gradient is removed; the texture is plain galvanised grey.
Model geometry unchanged. Turntable, parts board, close-ups and texture sheet are re-rendered.

## Faults from the gate before, all closed
1. Crest fence ended inside buildings: the fence is now split at every club wall, and each run ends at a wall within 5 cm
   (runs 0.2-93.6, 100.8-103.7, 138.8-139.5, 243.4-359.0 deg). Proof: zoom_crest_fence_meets_building, _between_buildings(_top).
2. North bank end at 139.5 deg: a short run from the whiteblock wall to the stand end. Proof: zoom_bank_meets_stand_north.
3. Board and turntable were stale: both re-rendered from this model.
4. Top-down overlay: done (topdown/). The club complex was re-planned from the satellite.
5. Bank height stays 3 m: in the 1993 panorama, standing heads on the bank reach the pavilion sign (4.2-5.0 m),
   which is 3 m of bank plus about 1.7 m of person.
6. Dark segments in the panorama (x 327-340, 355-368): read as dark-faced boards, not gates, because the board base and
   grass edge run on unbroken. The photo is too coarse to be certain.

Also fixed in this pass:
- Simulated crowd removed: billboards deleted, seats empty (zoom_seats_*_empty).
- Brick buildings have plain brick for the bottom 3.4 m and windows above. The bank had been cutting the lowest window row
  in half, and the 1993 panorama shows plain brick low down.
- Signs match the 1993 photo (sign_huggins, sign_pavilion).

No open faults.
