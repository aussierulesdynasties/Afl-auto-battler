# Adelaide Oval: the director's fault list (2026-11-21)

Paused 2026-11-21 (director, via the coordinator): all stadium effort goes into making the MCG the quality
standard first. Pick this list up again once that standard exists. Positions are as the ground inspector's C key
copies them ("x y z, facing, looking"); `godot ... GroundInspector.tscn -- --ground=adelaide --views=<file>`
re-shoots any list of them (one "name x y z facing looking" a line).

Generators: `.claude/review/adelaide/tools/gen.py` (stands, roofs, seats), `tools/hill.py` (the Hill),
`tools/hotel.py`; game export `tools/grounds/adelaide/paint.py` + `export.py` (README there).

| # | Where | What he saw | State |
| --- | --- | --- | --- |
| 1 | -1.3 62.1 169.6; -56.8 87.2 31.3; -117.0 116.8 -2.5 | Seats outside the stadium (behind the Riverbank roof, on the east stand's outer slope, behind the hotel deck) | Fixed: gen.py `seat_ok` places a seat only on a raked row, pitch-side of every roof or under one with 2.6 m headroom; a failing block-row goes whole. Riverbank stand ends at its roof, back glazed to the roof |
| 2, 5 | -53.7 15.4 27.6; -59.1 15.7 -28.8 | Gaps between the stands, chairs on the edge of the chasm with no barrier | Fixed: lower bowl runs round both south corners (spec `corner_se`, `corner_sw`; the Esri plan shows it continuous); a 1.1 m parapet on every raised stand end and back. The upper-tier gaps at the corners are real and stay |
| 3 | (lower bowl front) | Is this lip correct? | Fixed: the fence-front wall is now the dark wall of the photos (front_skin), not orange brick |
| 4 | -2.8 107.4 -114.1, facing 183, looking -70 | Is this (west) roof accurate? | Open: compare the five petals with photos/crop.jpg and close/west_stands_2023.jpg; the back edge was raised to 24.5 m for fault 9 |
| 6 | -3.1 32.4 -89.2; 7.3 63.3 -103.4 | Box building with two brick towers, flat slab overhanging, seats under it | Fixed: it is a real building (Esri plan, aerial photo: a flat-roofed block behind the petals between the towers). Now 17.45 m, its roof meeting the petals' back, towers 25 m, no seats in it |
| 7 | 75.7 6.0 -30.0, facing 60 | Hill seats were a painted slab | Fixed: 2,860 instanced seats on stepped treads (hill.py) |
| 8 | 86.3 17.2 -65.5, facing 2 | Oversized orange seats down the outside of the west stand's end wall; green roof underside | Fixed: the OSM notch at the stand's north end dropped (way_drop 20, 21). Roof underside green: global lighting fix in PR #1970 (MCG thread) |
| 9 | 37.8 18.1 -81.0; 19.4 17.5 -119.4 | Upper-tier rows uneven, running to the back where the roof crushes them | Fixed: west petals' back edge 24.5 m (back_west_2023), upper tier ends at the roof, the gap to the roof closed; flat decks never seated |
| 10 | 117.7 4.5 79.9, facing 327 | Scoreboard on a floating slab, flat black panel, paper-thin board on stilts | Fixed: the Hill is grassed down to the parkland all round; the amenities box sits on the mound; the screen is a 1.8 m solid cabinet with a bezel and back panels; the shelter roof is a solid slab |
| 11 | 85.1 35.8 26.9, facing 113 | Terrible texture work on the outer precinct | Partly fixed: 400 mm pavers (texture kind 1) with no streaks, kerbs round the grass patches, the worn patch is grass. Open: plants or trees, a real screen face, a full pass over the rest of the outer precinct |

Also open, found in our own fly-through: a pale rectangle inside the west upper tier at 37.8 18.1 -81.0 (looks
like one missing block of seats; seat_ok drops none there, so look at the tread or the lower tier showing through);
the east stand's back walls and north end exterior are plain concrete.
