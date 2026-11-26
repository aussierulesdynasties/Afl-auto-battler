class_name GroundModels
extends RefCounted
## Every ground's 3D model in the match view (row 202 2b): which model a ground plays in, and how
## it is laid on the match's ground so its boundary fence meets the one the match is played inside.
## The match view (Oval3D) and the stadium fly-through both build a ground through instantiate().
##
## A model lives in assets/grounds/<slug>/: <slug>.glb, or <slug>_part1.glb, _part2.glb ... when it
## is split under GitHub's 50 MB, plus optionally its seats drawn as one seat many times
## (MultiMesh): seat_tmpl.bin (or seat_tmpl_<colour>.bin for that colour) is the seat as float32
## triangles, seats_<colour>.bin a row-major 3x4 transform per seat, in the model's own metres.
## Seat legs drawn the same way (leg_tmpl.bin, legs_<colour>.bin) are part of the stand: nobody sits on them.

const DIR := "res://assets/grounds/"
## How far the fence stands outside the boundary line (Oval3D.FENCE).
const FENCE := 6.0
## A model mesh bigger than SLICE_OVER triangles is cut into SLICES pieces round the bowl (slice_big_meshes).
const SLICE_OVER := 200000
const SLICES := 32
## Grounds whose model is cut at a smaller size, and into how many pieces: [triangles over, pieces].
## The Gabba's 130,000-triangle bowl, drawn whole, cost more triangles than its 12 pieces cost draw
## calls (each piece is culled by the camera and by every shadow band on its own).
const SLICE_AT := {"gabba": [60000, 12]}
## A ground's seats are drawn in this many slices round the bowl, so only those in view are drawn.
const SEAT_SECTORS := 48
## The model sits this far under the match's turf, so its own grass never fights the turf for a pixel.
const UNDER_TURF := 0.1

## The ground (GameDB.ground_key) -> its model's folder.
const GROUNDS := {
	"MCG": "mcg", "Marvel Stadium": "marvel", "Optus Stadium": "optus", "SCG": "scg",
	"GMHBA Stadium": "gmhba", "People First Stadium": "people_first", "Engie Stadium": "engie",
	"Bellerive Oval": "bellerive", "Manuka Oval": "manuka", "Norwood Oval": "norwood",
	"Waverley Park": "waverley_park", "Windy Hill": "windy_hill", "Moorabbin Oval": "moorabbin",
	"Ikon Park": "ikon_park", "Whitten Oval": "whitten", "Football Park": "football_park",
	"Subiaco Oval": "subiaco", "WACA": "waca", "York Park": "york_park",
	"Cazaly's Stadium": "cazalys", "North Hobart Oval": "north_hobart", "Bruce Stadium": "bruce",
	"Riverway Stadium": "riverway", "Barossa Park": "barossa", "Sky Stadium": "sky",
	"Jiangwan Stadium": "jiangwan", "Hands Oval": "hands",
	"Blacktown International Sportspark": "blacktown", "Summit Park": "summit",
	"Macquarie Point Stadium": "macpoint", "Adelaide Oval": "adelaide", "The Gabba": "gabba",
	"Traeger Park": "traeger",
	"Mars Stadium": "mars",
}

## Each model's boundary fence, measured off the model (tools/grounds/fit_fence.py: an ellipse
## fitted to where a level line 0.5 m above the arena floor first meets the model, looking out
## from the middle): [centre x, centre z, arena floor y, long axis in degrees from +x towards +z,
## half length, half width], in the model's own metres. The MCG's floor is the 4.2 m its loader
## was built on (#1843); its drain line sits a metre lower. Bellerive and Windy Hill were refitted to
## the fence the game draws (tools/visual/preinspect_grounds.gd, 2026-11-21): the first fits left a
## stand up to 20 m inside Bellerive's boundary and Windy Hill's turned 6 degrees off. GMHBA's is the
## largest ellipse its front-row seats all stand outside (2026-11-22, the seat rule): the first fit ran
## through the Reg Hickey Stand's first three rows and the first row elsewhere.
const FIT := {
	"mcg": [0.53, 0.39, -4.2, -3.3, 87.19, 73.39],
	"marvel": [-0.02, -0.03, 5.4, 70.6, 90.45, 75.93],
	"optus": [-27.32, 5.16, 0.0, -11.07, 88.91, 69.92],   # bowl front ring from Google Earth (tools/grounds/optus/survey)
	"scg": [0.34, 6.68, 0.05, 85.8, 84.43, 72.25],
	"gmhba": [-9.4, 11.35, 0.02, -68.3, 93.02, 64.19],
	"people_first": [-0.72, 0.04, 0.02, -72.6, 89.11, 72.26],
	# ENGIE: an ellipse through the field edge traced from Google Earth (tools/grounds/engie/fit) gives the
	# centre and axis; its halves are a 162 x 126 m field plus FENCE, a metre inside the real 164 x 128, so
	# the game's fence runs 0.6 m (sides) to 3.2 m (ends) outside the grass edge and clears the front rows (2026-11-22).
	"engie": [-4.26, -3.6, 0.0, -44.0, 87.0, 69.0],
	"bellerive": [0.31, -0.64, -0.02, 68.7, 86.9, 66.77],
	# Manuka: rebuilt 2026-11-22 round the OSM pitch outline (tools/grounds/manuka/model); an ellipse fitted to that fence.
	"manuka": [4.68, 5.03, 0.0, -80.0, 85.94, 72.31],
	# Norwood: the rebuilt model (tools/grounds/norwood/model), origin the centre circle. Laid on the
	# painted boundary traced on Google Earth's top-down mosaic (2026-11-22): goal line to goal line
	# 163.9 m, 107.8 m across the flanks (published 165 x 110). The real boundary is squarer than any
	# ellipse and its flanks sit 2.5 m east of the goals' line, so this is the seat-safe ellipse with the
	# smallest worst miss: goals and centre square 2.4 m east of the real ones, flanks within 0.6 m
	# between the 50 m arcs, pockets 5-12 m inside the real line.
	"norwood": [2.4, 0.2, 0.0, 88.5, 87.93, 60.25],
	"waverley_park": [-1.08, 5.64, 0.0, -34.6, 92.9, 71.99],
	"windy_hill": [6.01, -11.01, 0.05, 1.4, 78.42, 67.69],
	"moorabbin": [0.88, -2.15, 0.0, -57.5, 86.73, 69.48],
	"ikon_park": [44.35, -22.32, 0.0, 10.1, 84.68, 73.85],
	"whitten": [146.34, -76.06, 0.0, -82.1, 96.9, 72.28],
	"football_park": [0.0, 0.0, 0.0, 90.0, 88.5, 72.5],
	"subiaco": [0.22, -10.44, 0.0, -0.7, 94.7, 67.63],
	"waca": [7.71, -1.58, 0.0, -3.6, 102.8, 71.36],
	"york_park": [-2.24, 0.38, 0.0, -64.6, 86.89, 70.56],
	"cazalys": [-1.21, 3.69, -0.01, 61.13, 87.49, 75.22],
	"north_hobart": [-6.71, 0.91, 0.0, -43.8, 81.59, 60.47],
	"bruce": [21.36, -39.57, 0.4, -56.7, 104.51, 64.28],
	"riverway": [-0.41, 1.12, 0.0, -89.9, 86.05, 72.72],
	# Traeger Park's fence is no full ring (none along the stand), so this is fitted to its turf
	# edge traced off Google Earth (tools/grounds/traeger/measure/outline_model.json), which the
	# fence follows (fix_r15.py), not by fit_fence.py.
	"traeger": [4.17, -8.65, -0.05, -91.82, 91.8, 73.94],
	# Barossa Park: the fence ellipse fitted to the grass edge traced on the 2026 mosaic (rms 0.31 m,
	# tools/grounds/barossa/plan.py FENCE).
	"barossa": [0.163, 0.467, 0.0, 72.716, 86.139, 65.766],
	# The other first drafts (#1930) are built round their fence: centre at the origin (Summit
	# 2 m off), floor 0. Jiangwan is a running-track stadium; its boundary was placed by judgement.
	"sky": [0.0, 0.0, 0.0, -77.7, 81.66, 63.74],
	"jiangwan": [0.0, 0.0, 0.0, 63.0, 84.0, 63.0],
	"hands": [0.0, 0.0, 0.0, -61.7, 92.51, 78.09],
	# Blacktown: the ellipse closest to its traced fence curve (tools/grounds/blacktown, 2026-11-22).
	"blacktown": [-4.86, -2.37, 0.0, 78.5, 85.15, 74.82],
	"summit": [-1.9, 0.75, 0.0, -83.5, 86.34, 76.17],
	"macpoint": [0.0, 0.0, 0.0, 35.0, 85.0, 72.0],
	# Adelaide Oval's model (#1856) exported for the game by tools/grounds/adelaide/export.py, and the
	# Gabba's model (tools/grounds/gabba), measured the same way.
	"adelaide": [-0.4, 1.37, 0.0, -102.0, 91.36, 65.7],
	"gabba": [2.47, 3.47, 0.0, 175.0, 86.88, 73.71],
	# Mars Stadium (tools/grounds/mars): its fence is one smooth curve fitted to Google Earth's straight-down
	# trace (qa/fit.py, 0.22 m rms), 169.4 x 139.0 m; this ellipse fits it to 0.45 m rms.
	"mars": [-5.4, 5.43, 0.0, -58.1, 84.07, 69.23],
}

## The land round a model that ends at its own street (in the model's metres): the ring from
## `inner` (under the model's paving) out past the horizon, at `y` just under its street, so the
## stadium does not stand on an island in an empty world. The MCG stands in Yarra Park: `map` is
## its ground painted from OpenStreetMap (tools/grounds/mcg/surrounds.py), `span` m a side round the
## model's middle, and `trees` the park's trees from the same map (x, z, height, canopy, shade).
## Barossa Park stands in its own land (tools/grounds/barossa/land.py): `land` is a model of the
## ground round it out to 1 km on its true heights (Lyndoch, the vineyards' rows, the houses), and
## its trees carry their own height (`trees_y`: x, y, z, height, canopy, shade) and draw as the
## ground's own gum trees (`gums`, tools/grounds/barossa/trees.py). `far_land` is the country on to
## 16 km (the Barossa Range on the skyline, tools/grounds/barossa/far.py), and `far` how far the match
## camera sees to show it.
const SURROUNDS := {
	# York Park: Invermay and the Inveresk precinct, the North Esk and the Tamar's east bank
	# (tools/grounds/york_park/surrounds.py), laid on the model's origin (the OSM pitch's centroid). It starts
	# past the fence everywhere, under the model's concourse.
	"york_park": {"y": -0.04, "inner": 92.0, "outer": 1024.0, "colour": Color(0.52, 0.51, 0.36),
			"map": "surrounds.webp", "span": 2048.0, "trees": "trees.bin", "buildings": "buildings.bin",
			# Invermay in Google Earth: white and cream weatherboard, red and brown brick, grey render,
			# pale showroom cladding.
			"walls": [Color(0.86, 0.85, 0.8), Color(0.62, 0.42, 0.34), Color(0.78, 0.74, 0.64), Color(0.56, 0.55, 0.52),
					Color(0.9, 0.9, 0.88), Color(0.66, 0.5, 0.4), Color(0.74, 0.76, 0.76)],
			# Its roofs from above: red and terracotta, charcoal, grey and white Colorbond, teal.
			"roofs": [Color(0.66, 0.3, 0.24), Color(0.36, 0.36, 0.38), Color(0.62, 0.62, 0.6), Color(0.8, 0.8, 0.78),
					Color(0.34, 0.5, 0.5), Color(0.56, 0.3, 0.24), Color(0.46, 0.48, 0.5), Color(0.72, 0.4, 0.3)]},
	# Bellerive: its streets and houses, Bellerive Beach, Kangaroo Bay and the Derwent
	# (tools/grounds/bellerive/surrounds.py), laid on the model's origin (the OSM pitch's centre). It starts under the
	# apron (88 m, past the fence everywhere): under the turf it z-fought from a blimp's height (grey bars).
	"bellerive": {"y": -0.04, "inner": 88.0, "outer": 1024.0, "colour": Color(0.5, 0.5, 0.34),
			"map": "surrounds.webp", "span": 2048.0, "trees": "trees.bin", "buildings": "buildings.bin",
			# The ground close round it at 0.375 m a pixel, 768 m a side (surrounds_near.webp): at 1 m a pixel
			# the yards and verges read as mush in close views (PC check r5).
			"near_map": "surrounds_near.webp", "near_span": 768.0,
			# Bellerive in Google Earth: white and cream weatherboard, red and brown brick, grey render.
			"walls": [Color(0.86, 0.85, 0.8), Color(0.62, 0.42, 0.34), Color(0.78, 0.74, 0.64), Color(0.56, 0.55, 0.52),
					Color(0.9, 0.9, 0.88), Color(0.66, 0.5, 0.4), Color(0.72, 0.76, 0.78)],
			# Each roof's own colour from above (Google Earth, tools/grounds/bellerive/houses_ge.py), linear.
			"roof_colours": "roofs.bin",
			# Its gums' crowns hang deep (Google Earth fac_200, out_SE): see _add_trees.
			"deep_crowns": true,
			# Its trees fill Google Earth's canopy (13,000 crowns): the far blocks draw a ball a crown (_add_trees).
			"tree_lod": true,
			# Its roofs from above: Colorbond teal and green, terracotta, charcoal, grey, white and blue.
			"roofs": [Color(0.32, 0.52, 0.5), Color(0.66, 0.34, 0.26), Color(0.36, 0.36, 0.38), Color(0.6, 0.6, 0.58),
					Color(0.4, 0.56, 0.44), Color(0.82, 0.82, 0.8), Color(0.44, 0.52, 0.62), Color(0.56, 0.3, 0.24)]},
	# Cazaly's: Westcourt and Parramatta Park, Mulgrave Road, Moody Creek (tools/grounds/cazalys/surr/surrounds.py),
	# laid on the model's origin (the OSM pitch's centroid); the ranges and the sea are its backdrop (surr/backdrop.py).
	"cazalys": {"y": -0.04, "inner": 95.0, "outer": 1024.0, "colour": Color(0.41, 0.47, 0.28),
			"map": "surrounds.webp", "span": 2048.0, "trees": "trees.bin", "buildings": "buildings.bin",
			# Westcourt in Google Earth: white and cream weatherboard Queenslanders, pastel and grey render, some brick.
			"walls": [Color(0.9, 0.9, 0.86), Color(0.86, 0.82, 0.7), Color(0.74, 0.8, 0.78), Color(0.9, 0.9, 0.86),
					Color(0.62, 0.44, 0.35), Color(0.7, 0.7, 0.68), Color(0.82, 0.78, 0.66)],
			# Its iron roofs from above: zincalume, off-white and grey Colorbond, a few green, red and blue.
			"roofs": [Color(0.6, 0.6, 0.58), Color(0.72, 0.72, 0.69), Color(0.42, 0.43, 0.44), Color(0.6, 0.6, 0.58),
					Color(0.32, 0.42, 0.35), Color(0.52, 0.27, 0.22), Color(0.72, 0.72, 0.69), Color(0.36, 0.42, 0.52)]},
	# GMHBA: Kardinia Park and Geelong's streets and houses (tools/grounds/gmhba/surrounds.py); the map is
	# laid on the model's origin, the stadium's own footprint painted plain under the model.
	"gmhba": {"y": -0.04, "inner": 60.0, "outer": 1024.0, "fence_margin": 4.0, "colour": Color(0.48, 0.49, 0.33),
			"map": "surrounds.webp", "span": 2048.0, "trees": "trees.bin", "tree_kind": "gum", "buildings": "buildings.bin",
			# Geelong's walls in Google Earth: red and brown brick, cream render, grey block, weatherboard.
			"walls": [Color(0.62, 0.42, 0.34), Color(0.74, 0.7, 0.62), Color(0.55, 0.53, 0.5), Color(0.68, 0.5, 0.4),
					Color(0.8, 0.78, 0.72), Color(0.6, 0.6, 0.6), Color(0.52, 0.36, 0.3)]},
	# People First: the Carrara precinct, the Nerang River, its bush and the streets round it
	# (tools/grounds/people_first/surrounds.py); the map laid on the model's origin. Drawn only while the
	# ground has no background scene: the scene covers the same land from 98 m out, in more detail.
	"people_first": {"fallback": true, "y": -0.04, "inner": 60.0, "colour": Color(0.41, 0.49, 0.3),
			"map": "surrounds.webp", "span": 2048.0, "trees": "trees.bin", "buildings": "buildings.bin",
			# Carrara's walls in Google Earth: cream and white render, pale brick, grey sheds.
			"walls": [Color(0.82, 0.8, 0.74), Color(0.72, 0.62, 0.52), Color(0.6, 0.6, 0.58), Color(0.88, 0.86, 0.82),
					Color(0.66, 0.5, 0.42), Color(0.74, 0.72, 0.68)]},
	# Norwood: Kent Town and Norwood's streets, villas, cottages and townhouses (tools/grounds/norwood/surrounds.py),
	# laid on the model's origin (the centre circle). The houses that face the ground are in the model itself.
	"norwood": {"y": -0.04, "inner": 60.0, "outer": 1024.0, "colour": Color(0.5, 0.49, 0.38),
			# The venue's own edge (the back of its walk) every 3.75 degrees (tools/grounds/norwood/model/arena.py).
			"inner_by_angle": [
				67.2, 68.0, 69.1, 70.6, 72.2, 74.0, 75.9, 77.9, 80.3, 82.8, 85.3, 87.7, 89.0, 91.2, 93.5, 95.5,
				97.4, 98.2, 98.9, 99.9, 100.3, 100.5, 100.6, 100.5, 100.1, 99.6, 98.9, 98.1, 97.0, 95.8, 94.4, 92.2,
				89.7, 87.1, 84.4, 81.6, 78.9, 77.3, 77.2, 74.4, 71.3, 68.7, 66.6, 65.1, 64.0, 63.3, 62.9, 62.7,
				62.8, 63.2, 63.8, 64.7, 66.0, 68.1, 70.8, 73.9, 77.7, 82.2, 86.2, 86.6, 87.6, 90.1, 92.4, 95.4,
				97.1, 98.1, 98.9, 99.6, 100.0, 100.2, 100.3, 100.2, 100.1, 99.2, 98.2, 97.1, 95.9, 94.5, 93.9, 92.3,
				90.6, 89.1, 87.4, 85.6, 83.6, 81.5, 79.3, 77.1, 74.9, 72.9, 71.1, 69.6, 68.3, 67.4, 66.9, 66.8],
			"map": "surrounds.webp", "span": 2048.0, "trees": "trees.bin", "buildings": "buildings.bin",
			# Norwood in Google Earth: bluestone and sandstone villa fronts, red brick, cream render, white townhouses.
			# (linear, as the vertex colours are read; each roof's own colour is in roofs.bin)
			"walls": [Color(0.181, 0.19, 0.199), Color(0.579, 0.428, 0.237), Color(0.349, 0.133, 0.082), Color(0.681, 0.612, 0.456),
					Color(0.793, 0.793, 0.755), Color(0.456, 0.279, 0.164), Color(0.279, 0.106, 0.071)],
			"roof_colours": "roofs.bin",
			# Its roofs from above: galvanised and Colorbond grey, charcoal, terracotta, red iron, pale zinc.
			"roofs": [Color(0.6, 0.6, 0.58), Color(0.36, 0.37, 0.39), Color(0.66, 0.36, 0.28), Color(0.56, 0.26, 0.22),
					Color(0.74, 0.74, 0.72), Color(0.46, 0.48, 0.47), Color(0.42, 0.5, 0.44), Color(0.82, 0.82, 0.8)]},
	# Mars: Ballarat North painted from OSM (tools/grounds/mars/surrounds/data.py), the canopy model's trees; its
	# houses, the workshops' chimney and the land out to the ranges are mars_part2.glb (build_bpy.py).
	"mars": {"y": -0.06, "inner": 95.0, "outer": 1900.0, "colour": Color(0.48, 0.5, 0.34),
			"map": "surrounds.webp", "span": 3840.0, "trees": "trees.bin"},
	# ENGIE: the showground, Olympic Boulevard and its plazas, the Brickpit and the parklands to Haslams Creek
	# painted from OpenStreetMap with every mapped tree (tools/grounds/engie/surrounds/surrounds.py); its
	# buildings are modelled in engie_part2.glb (surrounds/landmarks.py), so none are stood up here. It starts
	# under the stands (85 m), the stadium's paved site drawn over it by the model.
	"engie": {"y": -0.04, "inner": 85.0, "colour": Color(0.43, 0.46, 0.33),
			"map": "surrounds.webp", "span": 2048.0, "trees": "trees.bin"},
	"barossa": {"y": 0.0, "inner": 180.0, "land": "barossa_land.glb", "trees": "trees.bin", "trees_y": true,
			"gums": "barossa_gums.glb", "far_land": "barossa_far.glb", "far": 16000.0},
	"mcg": {"y": -0.03, "inner": 140.0, "colour": Color(0.45, 0.55, 0.27),
			"map": "surrounds.webp", "span": 2048.0, "trees": "trees.bin", "buildings": "buildings.bin",
			"outer": 1024.0},   # the background scene takes over from 1,024 m (reduce.py inner=1024)
	# Marvel Stadium in Docklands: Victoria Harbour, the Southern Cross rail yards, the streets and towers
	# round it from OpenStreetMap (tools/grounds/marvel/surrounds.py), and the Bolte Bridge's towers and
	# deck in 3D (tools/grounds/marvel/bridges.py).
	"marvel": {"y": -0.03, "inner": 120.0, "colour": Color(0.55, 0.56, 0.52),
			"map": "surrounds.webp", "span": 2048.0, "trees": "trees.bin", "buildings": "buildings.bin",
			"models": ["bridges.glb", "landmarks.glb"], "tint": Color(0.86, 0.84, 0.82), "building_tint": Color.WHITE, "building_style": "towers",
			# Round 12: the real land (terrain.bin, tools/grounds/marvel/land.py) right up to `inner`. The model's own
			# pad follows the same land, from 0.9 m under the old street by the harbour to 4.4 m over it on the east.
			"follow_land": true},
	# Adelaide Oval in the North Adelaide parklands: the River Torrens and Torrens Lake, Pennington and
	# Creswell Gardens, the CBD's towers to the south (tools/grounds/adelaide/surrounds.py), and in 3D
	# the Adelaide Oval footbridge, the river's other bridges and St Peter's Cathedral
	# (tools/grounds/adelaide/landmarks.py). The map starts under the stands (inner 105 m): the model's
	# own ground stops there, and inside it the match's turf and the model's floor take over.
	"adelaide": {"y": -0.03, "inner": 105.0, "outer": 1024.0, "colour": Color(0.45, 0.55, 0.27),
			"map": "surrounds.webp", "span": 2048.0, "trees": "trees.bin", "buildings": "buildings.bin",
			"models": ["landmarks.glb"], "building_colours": "buildings_col.bin",
			# The precinct and the parkland next to the stands at 4 pixels a metre (the far map's 1 m smeared
			# the concourse and paths seen from the stands: director's fault 11).
			"map_near": "surrounds_near.webp", "span_near": 512.0},
	# The Gabba in Woolloongabba: Vulture, Stanley and Main Streets, the Cross River Rail works, the East
	# Brisbane houses and yards, Kangaroo Point and the river, the CBD's towers to the north-west
	# (tools/grounds/gabba/surrounds.py).
	"gabba": {"y": -0.03, "inner": 100.0, "colour": Color(0.45, 0.55, 0.27),
			"map": "surrounds.webp", "span": 2048.0, "trees": "trees.bin", "buildings": "buildings.bin",
			"building_colours": "buildings_col.bin", "map_near": "surrounds_near.webp", "span_near": 512.0,
			"facades": 600.0},
	# The SCG in Moore Park: the park's dry grass and avenues of figs, Tramway Oval, the Entertainment
	# Quarter, Paddington's streets and Allianz Stadium's concourse from OpenStreetMap
	# (tools/grounds/scg/surrounds.py), and Allianz Stadium itself in 3D (tools/grounds/scg/allianz.py). Painted for the same match light as Optus's map.
	# inner 100: the stands' backs reach in to 100-110 m from the middle; at 120 the sky showed through
	# a gap between them and the land, a pale blue ring round the ground from above.
	"scg": {"y": -0.03, "inner": 100.0, "colour": Color(0.55, 0.56, 0.48),
			# Every building has modelled facades: those within 350 m in full (PARTS "Facades"), the rest
			# with recessed window ribbons in city.glb (tools/grounds/scg/facades.py; buildings.bin is its source).
			"map": "surrounds.webp", "span": 2048.0, "trees": "trees.bin",
			# The land rises 5-11 m east of the turf (Google Earth's own heights, tools/grounds/scg/relief.py);
			# the buildings, bridges and Allianz Stadium are stood on it by their tools, the trees here.
			"relief": "relief.bin",
			"models": ["allianz.glb", "city.glb"], "tint": Color(0.86, 0.84, 0.82)},
}

## Parts of a model drawn again from a build tool's own mesh (per vertex x, y, z, normal, colour;
## float32, the model's metres), the model's own nodes named in `hide` left out. The MCG's roof
## trusses are deep pale lattices from Google Earth, not the model's single blue beams
## (tools/grounds/mcg/trusses.py), and its outside walls get a slab edge at every floor
## (tools/grounds/mcg/ledges.py).
const PARTS := {
	"mcg": [{"mesh": "trusses.bin", "hide": ["trusses"], "name": "Trusses"},
			{"mesh": "ledges.bin", "name": "SlabEdges"}],
	# The SCG's boxes: a pale parapet and dark glass from each stand's top row to its roof, where the
	# model showed the back of a blank wall from the field (tools/grounds/scg/boxes.py).
	"scg": [{"mesh": "boxes.bin", "name": "Boxes"},
			# The north stands' two tier fronts: parapet, walkway and the dark void under the tier above
			# (tools/grounds/scg/tiers.py).
			{"mesh": "tiers.bin", "name": "TierFronts"},
			# The pale stair tower where the north stands meet the Members' (tools/grounds/scg/join.py).
			{"mesh": "join.bin", "name": "JoinTower"},
			# The buildings nearest the ground with real facades, windows set into piers and floor edges
			# (tools/grounds/scg/facades.py; they are out of buildings.bin).
			{"mesh": "facades.bin", "name": "Facades"},
			# Moore Park's footbridges over Anzac Parade (tools/grounds/scg/bridges.py).
			{"mesh": "bridges.bin", "name": "Bridges"},
			# The four big roofs (north, east, south, west), rebuilt on the front and back edges and the
			# heights measured on Google Earth (tools/grounds/scg/stand_roofs.py, qa/roof_ge.json).
			{"mesh": "roofs.bin", "name": "Roofs"}],
}

## Per-ground corrections to a model's materials, by material name, checked against Google Earth
## (MCG, 2026-11-21): the MCG's roof sheeting is matte grey from above. Built glossy and part metal,
## it mirrored the blue sky and read white-blue where the real roof reads warm grey; the tints bring
## its sunlit tops to Google Earth's colours (north 189,188,181, east 148,150,145).
const MATERIAL_FIX := {
	# Bellerive: the roof's underside and the stands' soffits read purple once the grass's green is taken
	# out of their light (the stand shader); Google Earth shows them a neutral dark grey. Roof sheeting matte.
	"bellerive": {
		"roof_soffit": {"albedo_color": Color(1.06, 0.98, 0.9)},
		"roof_white": {"metallic": 0.0, "roughness": 0.9},
		# The practice nets' veil is matte: glossy, it mirrored the sky and the roof net read as a sheet
		# of blue from above.
		"mesh": {"roughness": 1.0, "metallic_specular": 0.0},
	},
	# GMHBA (Google Earth 3D, 2026-11-22): the treads under the roofs were painted dark ("_d") and then shaded
	# again by the real roof, so they read near-black where the real rows read mid grey; the shade is the
	# renderer's job, so they take the sunlit tones back. Roof sheeting matte, as at the MCG.
	"gmhba": {
		# Solar panels: near-black in Google Earth, not a sky mirror.
		"solar": {"roughness": 0.85},
		"tread_d": {"albedo_color": Color(1.9, 1.9, 1.9)},
		"aisle_d": {"albedo_color": Color(1.6, 1.6, 1.6)},
		"tread": {"albedo_color": Color(1.15, 1.15, 1.12)},
		"roof": {"metallic": 0.0, "roughness": 0.9},
		"roofg": {"metallic": 0.0, "roughness": 0.9},
	},
	"mcg": {
		"roof_white": {"metallic": 0.0, "roughness": 0.9, "albedo_color": Color(0.84, 0.84, 0.8)},
		"roof_grey": {"metallic": 0.0, "roughness": 0.9, "albedo_color": Color(0.8, 0.8, 0.76)},
		"roof_teal": {"albedo_color": Color(0.72, 0.86, 0.8)},
		# The north stands' masts and ties: pale painted tubes in Google Earth, not dark galvanised.
		"steel_galv": {"metallic": 0.0, "roughness": 0.55, "albedo_color": Color(0.9, 0.9, 0.88)},
		# The front of each tier: Street View and a photo sphere on the ground show a pale concrete
		# parapet over a thin dark ribbon, not the near-black band the texture paints.
		"tier_fascia": {"albedo_color": Color(2.2, 2.2, 2.1)},
	},
	# Optus (2026-11-21, against Google Earth): the white PTFE roof is matte; built at roughness 0.6 it
	# took the sky's blue from every angle. The bronze fins (tools/grounds/optus/bronze.py) carry the slate
	# and warm streaks they show from the air; with no sky to mirror (the stand shader lights them), a
	# metal only turned them black in shade (2026-11-22), so they stay nearly matte.
	"optus": {
		"roof": {"metallic": 0.0, "roughness": 0.95, "albedo_color": Color(0.97, 0.96, 0.93)},
		"bronze": {"metallic": 0.1, "roughness": 0.5},
		"sign_a": {"metallic": 0.1, "roughness": 0.5},
		# The glass storeys read blue-teal grey from outside in daylight (bronze.py glass), not sky blue.
		"glass": {"metallic": 0.1, "roughness": 0.3},
	},
	# SCG (2026-11-22, against Google Earth): the roofs are matte pale grey, not glossy white that takes
	# the sky's blue; the heritage stands' roofs a pale weathered sage, not bright green; the glass
	# blue-grey behind pale mullions, not deep blue.
	"scg": {
		# warm white: Google Earth's (238, 235, 222); the match light's sky had turned (0.84, 0.83, 0.8) pale blue
		"roof": {"metallic": 0.0, "roughness": 0.95, "albedo_color": Color(0.88, 0.85, 0.77)},
		"fascia": {"metallic": 0.0, "roughness": 0.9},
		"hroof": {"metallic": 0.0, "roughness": 0.85, "albedo_color": Color(2.0, 1.2, 1.75)},
		"hgreen": {"albedo_color": Color(2.0, 1.2, 1.75)},
		"glasst": {"metallic": 0.0, "roughness": 0.6, "albedo_color": Color(1.45, 0.88, 0.58)},
		"glass": {"metallic": 0.0, "roughness": 0.6, "albedo_color": Color(0.95, 0.88, 0.8)},
		"glassd": {"metallic": 0.0, "roughness": 0.6, "albedo_color": Color(1.0, 0.93, 0.85)},
		"glassroof": {"metallic": 0.0, "roughness": 0.4},
		# The concourse paving round the stands: Google Earth's warm grey concrete (155, 148, 138), as the
		# map paints the forecourts beyond it (tools/grounds/scg/surrounds.py CONCOURSE), not near-white.
		"conc": {"metallic": 0.0, "roughness": 1.0, "albedo_color": Color(0.6, 0.56, 0.5)},
		"podium": {"metallic": 0.0, "roughness": 1.0, "albedo_color": Color(0.62, 0.58, 0.52)},
	},
}

## Grounds with a roof that opens: the model's node for the roof shut over the field and the node for
## it slid back, of which instantiate() shows one. Marvel Stadium plays AFL with its roof shut (as the
## match scenes draw it, data/grounds.json "roof": "closed"); the fly-through can open it (set_roof).
## Shut, the stadium casts no sun shadow: under it the ground is lit by the roof's own lights. Looks only.
const ROOFS := {"marvel": {"shut": "roofshut", "open": "roofopen"}}

## Models that carry their colours on the vertices (glTF COLOR_0) under a tiling detail texture.
## Godot's glTF reader keeps the colours but does not paint with them, so the loader turns that on.
const VERTEX_COLOURED := ["adelaide"]

## Grounds whose seats throw no shadows (see _instances).
const SEATS_NO_SHADOW := ["bellerive"]
## Grounds whose seats turn into far rows (_seat_far_mesh) between SEAT_FAR_FROM and SEAT_FAR_TO m.
const SEAT_FAR_SHADER := preload("res://scripts/ui/match/seat_far.gdshader")
const SEAT_NEAR_SHADER := preload("res://scripts/ui/match/seat_near.gdshader")
const SURROUNDS_SHADER := preload("res://scripts/ui/match/surrounds_ground.gdshader")
const SEAT_FAR := ["bellerive"]
const SEAT_FAR_FROM := 40.0
const SEAT_FAR_TO := 70.0

## Each seat colour as the model paints it (the mean of its seat texture; sRGB).
const SEAT_COLOURS := {
	# Mars Stadium (seat_blue and seat_greyblue there keep the values already here).
	"seat_cream": Color(0.785, 0.747, 0.655), "seat_white": Color(0.815, 0.830, 0.845),
	"seat_navyblue": Color(0.157, 0.235, 0.502), "seat_charcoal": Color(0.141, 0.165, 0.227),
	"seat_slategrey": Color(0.361, 0.392, 0.447), "seat_lightgrey": Color(0.698, 0.714, 0.737),
	# Accor: aqua lower bowl (seat_teal there keeps the value already here).
	"seat_aqua": Color(0.527, 0.719, 0.757),
	# Bellerive: pale grey-blue plastic all round the Boon and Ponting stands, the sunlit seats'
	# median in Google Earth from the field (PC seat checks 2026-11-23: 72,108,146 and 100,130,158 read too blue;
	# 108,142,160 read N 77,108,129 against GE 91,129,140 and E 56,94,123 against 58,97,113: red and green up a ninth).
	"seat_bel_blue": Color8(120, 158, 160),
	# The Members' front rows dark grey; the Northern Stand's and the east terrace's benches white.
	"seat_bel_pale": Color8(150, 168, 186), "seat_bel_dark": Color8(58, 62, 70), "seat_bel_white": Color8(214, 216, 214),
	# Manuka (Google Earth from the field, 2026-11-22): pale grey front terraces, white Bradman, red east terraces,
	# and the A-frame stands' scattered reds, oranges, blues, greys, teals and yellows.
	"seat_mk_pale": Color8(196, 198, 196), "seat_mk_white": Color8(226, 228, 226), "seat_mk_red": Color8(176, 40, 42),
	"seat_mk_orange": Color8(214, 108, 42), "seat_mk_blue": Color8(44, 84, 150), "seat_mk_grey": Color8(112, 116, 122),
	"seat_mk_teal": Color8(38, 128, 138), "seat_mk_yellow": Color8(222, 182, 44),
	# GMHBA, from photo p12: blue and white shells in pairs (tools/grounds/gmhba/post/post.py).
	"seat_gmhba_blue": Color8(52, 60, 74), "seat_gmhba_white": Color8(172, 176, 180),
	# MCG, by tier from Street View on the ground and Google Earth: white and light grey lower and
	# middle tiers, a blue band along the front of the middle tier, teal-blue top tier
	# (grey-green in the Members' north-west).
	"seat_mcg_white": Color(0.96, 0.88, 0.80), "seat_mcg_grey": Color(0.76, 0.70, 0.64),
	"seat_mcg_blue": Color(0.18, 0.32, 0.52), "seat_mcg_teal": Color(0.42, 0.64, 0.66),
	"seat_mcg_sage": Color(0.50, 0.58, 0.56),
	# Marvel Stadium by level (tools/grounds/marvel/seats.py): neutral grey, as photos of the bowl show them (2026-11-22).
	"seat_marvel_lo": Color8(110, 112, 116), "seat_marvel_mid": Color8(110, 112, 116), "seat_marvel_up": Color8(110, 112, 116),
	"seat_marvel_mred": Color8(196, 28, 36), "seat_marvel_mwhite": Color8(232, 232, 228),
	# The front of the lower tier from the Members' round to the north: green (a photo sphere on the ground).
	"seat_mcg_green": Color(0.46, 0.70, 0.58),
	"seat_green": Color(0.314, 0.549, 0.455), "seat_teal": Color(0.384, 0.620, 0.541),
	"seat_blue": Color(0.2, 0.318, 0.467), "seat_paleblue": Color(0.482, 0.612, 0.714),
	"seat_mint": Color(0.502, 0.706, 0.655), "seat_dkgreen": Color(0.039, 0.243, 0.125),
	"seat_greyblue": Color(0.361, 0.471, 0.525),
	"s_blue": Color(0.211, 0.28, 0.448), "s_orange": Color(0.785, 0.426, 0.158),
	"s_grey": Color(0.64, 0.648, 0.663), "s_maroon": Color(0.443, 0.129, 0.16),
	"s_gold": Color(0.863, 0.649, 0.129), "s_teal": Color(0.135, 0.479, 0.456),
	# Optus: each tier's colour pushed grey-blue or tan (optus build.py), the whole bowl then scaled (two passes) so the
	# sunlit west seats match Google Earth's colour on a PC render under the same sun (tools/grounds/optus).
	"seat_lo_blue": Color(0.411, 0.544, 0.550), "seat_lo_tan": Color(0.459, 0.556, 0.489),
	"seat_mid_blue": Color(0.475, 0.580, 0.518), "seat_mid_tan": Color(0.518, 0.592, 0.457),
	"seat_up_blue": Color(0.330, 0.473, 0.510), "seat_up_tan": Color(0.378, 0.485, 0.450),
	# ENGIE Stadium: red tip-up seats on black shells with the odd orange one under the roofs, orange with
	# some red at the open north-east end (a photo sphere in the stands, Jan 2019).
	"seat_engie_red": Color8(206, 44, 40), "seat_engie_orange": Color8(232, 112, 36),
	"seat_engie_shell": Color8(34, 34, 36),
	# York Park's teal-green plastic (york_park/model/paint.py), the SCG's two seat colours
	# (their glb material colours, linear -> sRGB).
	"seat_plastic": Color(0.255, 0.365, 0.33),
	# Barossa Park: the bright blue seats of Gather Round's temporary stands (the 2026 match photo).
	"seat_barossa_blue": Color(0.12, 0.29, 0.62),
	# The SCG's teal: lighter and greener than its glb material, as the seats read in Google Earth
	# and photos of the ground in daylight (2026-11-22).
	"seat_scg_teal": Color(0.22, 0.55, 0.49), "seat_scg_maroon": Color(0.443, 0.125, 0.163),
	# The seven first drafts (#1930; Jiangwan and Summit have no seats).
	"seat_hands": Color(0.151, 0.319, 0.502),
	"seat_sky_gold": Color(0.778, 0.609, 0.197), "seat_sky_grey": Color(0.266, 0.281, 0.304),
	"seat_bt": Color(0.173, 0.18, 0.196), "seat_mp": Color(0.219, 0.25, 0.296),
	# Adelaide Oval's stand colours, as its model paints them (tools/grounds/adelaide/export.py).
	"seat_ao_navy": Color8(35, 55, 77), "seat_ao_charcoal": Color8(70, 70, 75),
	"seat_ao_slate": Color8(100, 116, 114), "seat_ao_sage": Color8(95, 118, 112),
	"seat_ao_red": Color8(150, 45, 50), "seat_ao_orange": Color8(200, 62, 36),
	# The Gabba's seats (tools/grounds/gabba/build.py v7, from a 2019 photo sphere on the ground): gold above all,
	# maroon in whole blocks, some white; and its steel seat legs.
	"seat_gabba_gold": Color8(226, 168, 30), "seat_gabba_maroon": Color8(112, 30, 46),
	"seat_gabba_white": Color8(236, 236, 230),
	"gabba_steel": Color(0.45, 0.46, 0.47),
	# Norwood (AFLW 2025 photos 01 and 23): the Sir Edwin Smith Stand's green and blue plastic and its
	# timber benches; the Western Stand's teal with its red blocks (Google Earth).
	"seat_nw_green": Color8(46, 112, 74), "seat_nw_blue": Color8(38, 72, 138), "seat_nw_timber": Color8(150, 84, 50),
	"seat_nw_teal": Color8(70, 124, 134), "seat_nw_red": Color8(168, 44, 40),
}


## The model folder a match at `ground` plays in, "" when the ground has no model yet.
static func slug_for(ground: String) -> String:
	if GROUNDS.has(ground):
		return str(GROUNDS[ground])
	# GameDB through the tree, so tools that load this before the autoloads still compile.
	var tree := Engine.get_main_loop() as SceneTree
	var db: Node = tree.root.get_node_or_null("GameDB") if tree != null else null
	return str(GROUNDS.get(db.ground_key(ground), "")) if db != null else ""


## The ground's name for a model folder ("MCG" for mcg), as a screen writes it.
static func ground_name(slug: String) -> String:
	for g: String in GROUNDS:
		if str(GROUNDS[g]) == slug:
			return g
	return slug


## The match's boundary fence now: half its length and width (the playing surface plus FENCE).
static func match_fence() -> Vector2:
	return Vector2(MatchMotion.HALF_LEN + FENCE, MatchMotion.HALF_WID + FENCE)


## The playing surface of the model `slug`, half its length and width: its own fence (FIT)
## less FENCE, so the model is laid at its own size with nothing stretched. Vector2.ZERO when
## the model has no measured fence.
static func field(slug: String) -> Vector2:
	if not FIT.has(slug):
		return Vector2.ZERO
	var f: Array = FIT[slug]
	return Vector2(float(f[4]) - FENCE, float(f[5]) - FENCE)


static var _published := {}   # data/grounds.json's grounds, read once (not VignetteGround: no autoloads here)


## The playing surface a match at `ground` is played on, half its length and width: its model's
## (field) where it has one, else its published size (data/grounds.json, as the vignettes draw
## it), else Vector2.ZERO, the standard oval (MatchMotion.use_field).
static func field_for(ground: String) -> Vector2:
	if ground == "":
		return Vector2.ZERO
	var slug := slug_for(ground)
	if slug != "" and FIT.has(slug):
		return field(slug)
	if _published.is_empty():
		var parsed = JSON.parse_string(FileAccess.get_file_as_string("res://data/grounds.json"))
		_published = (parsed as Dictionary).get("grounds", {}) if parsed is Dictionary else {"": {}}
	var own: Dictionary = _published.get(ground, {})
	if not (own.has("length") and own.has("width")):
		return Vector2.ZERO
	return Vector2(float(own["length"]), float(own["width"])) * 0.5


static var _traced := {}   # data/ground_boundaries.json's grounds, read once


## The traced boundary of the model `slug` (data/ground_boundaries.json, tools/grounds/boundary/fit_boundary.py):
## "frame" [x, z, degrees] the goals' midpoint and the line through them in the model's metres, "goal_x" half
## the distance between the goal lines, "boundary" the line's Fourier radius about that midpoint, "fence" the
## fence's where it was traced too. {} where the ground's boundary has not been traced yet (it plays on the
## ellipse its FIT row gives).
static func shape_for(slug: String) -> Dictionary:
	if _traced.is_empty():
		var parsed = JSON.parse_string(FileAccess.get_file_as_string("res://data/ground_boundaries.json"))
		_traced = (parsed as Dictionary).get("grounds", {}) if parsed is Dictionary else {}
		if _traced.is_empty():
			_traced = {"": {}}
	return _traced.get(slug, {})


## Play the match at `ground` on its own field (MatchMotion.use_field), and on its traced boundary line and goals
## where it has them (MatchMotion.use_shape). Every match, the fly-through and the tests set the ground up here.
static func play_at(ground: String) -> void:
	play_on(slug_for(ground) if ground != "" else "", field_for(ground))


## ...the same by the model's folder, `half` the field size to fall back on.
static func play_on(slug: String, half: Vector2) -> void:
	MatchMotion.use_field(half)
	var sh := shape_for(slug) if slug != "" else {}
	if not sh.is_empty():
		MatchMotion.use_shape(PackedFloat32Array(sh["boundary"]), float(sh["goal_x"]))


## The fence (grass edge) of the ground the match is on, as a Fourier radius in the match's frame, where it was
## traced; else the boundary line FENCE further out (or empty on an untraced ground: the ellipse match_fence()).
static func match_fence_shape(slug: String) -> PackedFloat32Array:
	if not MatchMotion.shaped():
		return PackedFloat32Array()
	var sh := shape_for(slug)
	if sh.has("fence"):
		return PackedFloat32Array(sh["fence"])
	var f := MatchMotion.SHAPE.duplicate()
	f[0] += FENCE
	return f


## Every ground that has a model, by its name.
static func grounds() -> Array:
	return GROUNDS.keys()


## How the model is laid on the match ground: its fence centre to the middle, its arena floor just
## under the turf, its long axis along the ground (x), and scaled so its fence meets the match's
## fence (stretch(): none when the match is on the model's own field, as it always is in play).
static func fit_transform(slug: String) -> Transform3D:
	if not FIT.has(slug):
		return Transform3D.IDENTITY
	var f: Array = FIT[slug]
	var s := stretch(slug)
	var turn := float(f[3])
	var centre := Vector3(float(f[0]), float(f[2]), float(f[1]))
	# A traced ground is laid on its real goals: their midpoint to the middle, the line through them along x,
	# and nothing stretched (the match plays on that very line, MatchMotion.use_shape).
	var sh := shape_for(slug)
	if not sh.is_empty():
		var fr: Array = sh["frame"]
		centre = Vector3(float(fr[0]), float(f[2]), float(fr[1]))
		turn = float(fr[2])
		s = Vector2.ONE
	var basis := Basis.from_scale(Vector3(s.x, 1.0, s.y)) * Basis(Vector3.UP, deg_to_rad(turn))
	return Transform3D(basis, -(basis * centre) - Vector3(0.0, UNDER_TURF, 0.0))


## How much the model is stretched along (x) and across (y) the ground to meet the match's fence:
## none (1, 1) when the match is played on the model's own field (MatchMotion.use_field(field())),
## as every match and the fly-through are.
static func stretch(slug: String) -> Vector2:
	var fence := match_fence()
	var f: Array = FIT.get(slug, [0, 0, 0, 0, fence.x, fence.y])
	return Vector2(fence.x / float(f[4]), fence.y / float(f[5]))


## The model's glb files: <slug>.glb, or its pieces <slug>_part1.glb, _part2.glb ...
static func files(slug: String, base := "") -> PackedStringArray:
	var dir := base if base != "" else DIR + slug + "/"
	var out := PackedStringArray()
	if ResourceLoader.exists(dir + slug + ".glb") or FileAccess.file_exists(dir + slug + ".glb"):
		out.append(dir + slug + ".glb")
		return out
	var k := 1
	while true:
		var p := dir + "%s_part%d.glb" % [slug, k]
		if not (ResourceLoader.exists(p) or FileAccess.file_exists(p)):
			break
		out.append(p)
		k += 1
	return out


## A glb as a scene: an imported res:// path loads normally; any other path (a .gdignored
## folder, an absolute file) is read straight off disk.
static func load_glb(path: String) -> Node3D:
	if ResourceLoader.exists(path):
		var scene := load(path) as PackedScene
		if scene != null:
			return scene.instantiate() as Node3D
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	if doc.append_from_file(ProjectSettings.globalize_path(path), state) != OK:
		push_error("GroundModels: cannot read %s" % path)
		return null
	return doc.generate_scene(state) as Node3D


## The ground `slug` built and laid on the match ground (fit_transform): its model and its seats.
## `base` reads the model from another folder (the fly-through's review folders); "" is
## assets/grounds/<slug>/. No crowd: the seats are empty (director, 2026-11-19).
static func instantiate(slug: String, base := "") -> Node3D:
	var dir := base if base != "" else DIR + slug + "/"
	var root := Node3D.new()
	root.name = "Ground"
	root.transform = fit_transform(slug)
	for path in files(slug, dir):
		var model := load_glb(path)
		if model != null:
			if slug in VERTEX_COLOURED:
				_paint_vertex_colours(model)
			if MATERIAL_FIX.has(slug):
				_fix_materials(model, MATERIAL_FIX[slug])
			_plain_alpha(model)
			if OPEN_GROUND.has(slug):
				_open_ground(model, OPEN_GROUND[slug])
			for part: Dictionary in PARTS.get(slug, []):
				_add_part(model, dir, part)
			# A mesh named nocast_* (Marvel's truss webs, 0.32 m members) casts no shadow: under a texel of the
			# sun's shadow map, its shadows broke into blue-white speckle across the roof (PC check 2026-11-23)
			for mi in model.find_children("nocast*", "GeometryInstance3D", true, false):
				(mi as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			root.add_child(model)
	slice_big_meshes(root, SLICE_AT.get(slug, [SLICE_OVER, SLICES]))
	var fit: Array = FIT.get(slug, [0.0, 0.0])
	_add_seats(root, dir, Vector2(float(fit[0]), float(fit[1])))
	if ROOFS.has(slug):
		set_roof(root, slug, true)
	# A "fallback" ring stands in only until the ground's background scene (#2023) is in the game.
	if SURROUNDS.has(slug) and not (SURROUNDS[slug].get("fallback", false)
			and not files(slug + "_backdrop", dir).is_empty()):
		_add_surrounds(root, SURROUNDS[slug], dir, FIT.get(slug, []),
				GroundTerrain.load_for(dir, FIT.get(slug, [])))
	var bd := backdrop(slug, dir)
	if bd != null:
		root.add_child(bd)
		for n: String in BACKDROP_HIDES.get(slug, []):   # the model's own ground, where the scene's takes over
			for mi in root.find_children(n + "*", "MeshInstance3D", true, false):
				(mi as MeshInstance3D).visible = false
	return root


## A ring of parkland round the model (SURROUNDS): grass with a broad mottle, unlit by
## nothing it would not be lit by (it takes the sun, the sky and the stands' shade). With the
## ground's real land (`land`, tools/grounds/terrain) the ring follows it, a dense ring every
## LAND_STEP m, and its trees and buildings stand on it; it never rises above the model's street
## at `inner`, banking up to the real land over LAND_BANK m. A ground with its own land model
## (SURROUNDS `land`) draws that instead.
static func _add_surrounds(root: Node3D, s: Dictionary, dir := "", fit: Array = [],
		land: GroundTerrain = null) -> void:
	if s.has("land"):
		_add_land(root, s, dir)
		return
	var inner: float = s["inner"]
	# "fence_margin": the ring starts that far past the field's fence instead of on a circle, so it never
	# lies under the turf (from high up the two fought in bars) yet still reaches under the model's apron
	# where the street comes close (GMHBA's Moorabool Street side).
	var margin: float = s.get("fence_margin", -1.0)
	var outer: float = s.get("outer", 2500.0)
	# Where the ground's background scene takes over (`outer` given): the map's square corners reach past
	# the ring, so its trees and buildings stop on the same circle, never drawn twice with the scene's.
	var reach: float = outer if s.has("outer") else INF
	var y: float = s["y"]
	var by_angle: Array = s.get("inner_by_angle", [])
	var n := 96 if by_angle.is_empty() else by_angle.size()
	if land != null:
		n = 360
	var map: Texture2D = null
	if s.has("map") and ResourceLoader.exists(dir + str(s["map"])):
		map = load(dir + str(s["map"]))
	var span: float = s.get("span", 2048.0)
	# `map_near`: the land next to the stands painted finer (`span_near` m a side), drawn out to just inside its
	# edge; the far map's ring starts where it stops, on the same vertices, so the two meet without a seam.
	var near: Texture2D = null
	if map != null and s.has("map_near") and ResourceLoader.exists(dir + str(s["map_near"])):
		near = load(dir + str(s["map_near"]))
	var span_near: float = s.get("span_near", 512.0)
	var r_near := span_near / 2.0 - 2.0
	# `relief`: the land's own rise and fall (relief_at), on rings close enough to follow it.
	var relief := PackedFloat32Array()
	if s.has("relief") and FileAccess.file_exists(dir + str(s["relief"])):
		relief = FileAccess.get_file_as_bytes(dir + str(s["relief"])).to_float32_array()
	if not relief.is_empty():
		n = RELIEF_SIDES
	# Where the land starts along `d`, the `i`th of the n directions round.
	var start := func(i: int, d: Vector3) -> float:
		var first := inner
		if margin >= 0.0 and fit.size() >= 6:
			first = _past_fence(d, fit, margin)
		# A venue that is not round ends where its own ground ends: inner_by_angle gives that edge (m) every
		# 360/n degrees from +x toward +z; the land starts half a metre inside it, under the model's ground.
		if by_angle.is_empty():
			return first
		# The ring may have more directions than the list (360 on the real land): read the edge between
		# its entries by angle, never by index, or a 96-entry list wrapped 3.75 times round in spikes.
		var t := float(i) * by_angle.size() / n
		var k := int(t)
		return lerpf(float(by_angle[k % by_angle.size()]), float(by_angle[(k + 1) % by_angle.size()]), t - k) - 0.5
	var radii := func(i: int, d: Vector3) -> Array:
		var r0: float = start.call(i, d)
		var rs: Array = RINGS.map(func(f): return f if f > 0.0 else r0) + [outer]
		if not relief.is_empty():
			rs = []
			var r := r0
			while r < RELIEF_REACH:
				rs.append(r)
				r += RELIEF_RING if r < 600.0 else RELIEF_RING * 2.0
			rs.append_array([RELIEF_REACH, outer])
		if land != null:
			# The same rings on every spoke, each `off` past where that spoke starts: _ring_mesh joins
			# ring k of one spoke to ring k of the next, so a spoke with more rings than its neighbour
			# (the venue's edge varies 63-100 m round Norwood) tore the ring into spikes over the turf.
			rs = []
			var off := 0.0
			while inner + off < outer - 100.0:
				rs.append(r0 + off)
				var q := inner + off
				off += LAND_STEP if q < inner + 300.0 else (LAND_STEP * 3.0 if q < inner + 900.0 else LAND_STEP * 10.0)
			rs.append(outer)
		if near != null:
			rs = [r_near] + rs.filter(func(r): return r > r_near + 1.0)
		return rs
	var follow: bool = s.get("follow_land", false)
	var mesh := _ring_mesh(radii, n, y, span if map != null else -60.0, relief, land, inner, follow)
	if map != null:
		var mm := StandardMaterial3D.new()
		mm.resource_name = "surrounds"
		mm.albedo_texture = map
		# The sun's shadow map reaches 160 m from the camera; past it, on the Mobile renderer, the
		# land read as if in shade (blue-grey). Its trees' shade is painted into the map instead.
		mm.disable_receive_shadows = true
		mm.texture_repeat = false
		mm.roughness = 1.0
		# `tint` brings the painted map to Google Earth's colours under the match light.
		mm.albedo_color = s.get("tint", Color.WHITE)
		var mat: Material = mm
		if s.has("near_map") and ResourceLoader.exists(dir + str(s["near_map"])):
			var sm := ShaderMaterial.new()
			sm.shader = SURROUNDS_SHADER
			sm.resource_name = "surrounds"
			sm.set_shader_parameter("far_map", map)
			sm.set_shader_parameter("near_map", load(dir + str(s["near_map"])))
			sm.set_shader_parameter("span", span)
			sm.set_shader_parameter("near_span", float(s.get("near_span", 768.0)))
			mat = sm
		var g := MeshInstance3D.new()
		g.name = "Surrounds"
		g.mesh = mesh
		g.material_override = mat
		g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		g.set_meta("open_ground", true)
		root.add_child(g)
		if near != null:
			var nm := mm.duplicate() as StandardMaterial3D
			nm.resource_name = "surrounds_near"
			nm.albedo_texture = near
			var gn := MeshInstance3D.new()
			gn.name = "SurroundsNear"
			gn.mesh = _ring_mesh(func(i, d): return [start.call(i, d), r_near], n, y, span_near, relief, land, inner, follow)
			gn.material_override = nm
			gn.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			gn.set_meta("open_ground", true)
			root.add_child(gn)
		if s.has("trees") and FileAccess.file_exists(dir + str(s["trees"])):
			_add_trees(root, FileAccess.get_file_as_bytes(dir + str(s["trees"])).to_float32_array(), y, 5,
					str(s.get("tree_kind", "")), bool(s.get("deep_crowns", false)), bool(s.get("tree_lod", false)),
					relief, land, reach)
		if s.has("buildings") and FileAccess.file_exists(dir + str(s["buildings"])):
			# `building_colours`: each building's wall and roof colour (6 bytes, the map's order), from
			# OpenStreetMap's building:colour and roof:colour where mapped (Adelaide).
			var bcol := PackedByteArray()
			if s.has("building_colours") and FileAccess.file_exists(dir + str(s["building_colours"])):
				bcol = FileAccess.get_file_as_bytes(dir + str(s["building_colours"]))
			var rgb := PackedFloat32Array()
			if s.has("roof_colours") and FileAccess.file_exists(dir + str(s["roof_colours"])):
				rgb = FileAccess.get_file_as_bytes(dir + str(s["roof_colours"])).to_float32_array()
			_add_buildings(root, FileAccess.get_file_as_bytes(dir + str(s["buildings"])).to_float32_array(), y,
					s.get("walls", []), s.get("roofs", []), rgb, s.get("building_tint", s.get("tint", Color.WHITE)),
					bcol, float(s.get("facades", 0.0)),
					str(s.get("building_style", "")), land, reach)
		for m in s.get("models", []):
			var extra := load_glb(dir + str(m))
			if extra != null:
				extra.name = str(m).get_basename()
				for gi in extra.find_children("*", "GeometryInstance3D", true, false):
					(gi as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				root.add_child(extra)
		return
	var noise := FastNoiseLite.new()
	noise.frequency = 0.02
	noise.seed = 7
	var tex := NoiseTexture2D.new()
	tex.noise = noise
	tex.seamless = true
	tex.width = 256
	tex.height = 256
	var grad := Gradient.new()
	var c: Color = s["colour"]
	grad.set_color(0, c.darkened(0.18))
	grad.set_color(1, c.lightened(0.1))
	tex.color_ramp = grad
	var mat := StandardMaterial3D.new()
	mat.resource_name = "surrounds"
	mat.albedo_texture = tex
	mat.roughness = 1.0
	var mi := MeshInstance3D.new()
	mi.name = "Surrounds"
	mi.mesh = mesh
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(mi)


## A flat ring at height `y`, `n` steps round: `radii.call(i, d)` gives its radii (m from the model's middle)
## along `d`, the `i`th direction, the same number each way. UVs: a painted
## map `span` m a side centred on the middle (clamped at its edge), or for a negative span a texture
## tiling every -span m. With `relief` the ring follows the land's rise and fall (relief_at); with
## `land` it follows the real land, banked up to it from `y` at `inner` (or on it throughout, `follow`).
static func _ring_mesh(radii: Callable, n: int, y: float, span: float,
		relief := PackedFloat32Array(), land: GroundTerrain = null, inner := 0.0, follow := false) -> ArrayMesh:
	var v := PackedVector3Array()
	var uv := PackedVector2Array()
	var nrm := PackedVector3Array()
	var idx := PackedInt32Array()
	var per := 0
	for i in n + 1:
		var a := TAU * i / n
		var d := Vector3(cos(a), 0.0, sin(a))
		var rs: Array = radii.call(i, d)
		per = rs.size()
		for r: float in rs:
			var p := d * r + Vector3(0.0, y, 0.0)
			var up := Vector3.UP
			if not relief.is_empty():
				p.y += relief_at(relief, p.x, p.z)
				var gx := relief_at(relief, p.x + 2.0, p.z) - relief_at(relief, p.x - 2.0, p.z)
				var gz := relief_at(relief, p.x, p.z + 2.0) - relief_at(relief, p.x, p.z - 2.0)
				up = Vector3(-gx, 4.0, -gz).normalized()
			if land != null:
				var real := land.height(p.x, p.z) - 0.03
				var w := smoothstep(inner, inner + LAND_BANK, r)
				p.y = real if follow else lerpf(minf(real, y), real, w)
			v.append(p)
			uv.append(Vector2(p.x, p.z) / span + Vector2(0.5, 0.5) if span > 0.0 else Vector2(p.x, p.z) / -span)
			nrm.append(up)
	for i in n:
		for k in per - 1:
			var a0 := i * per + k
			var b0 := (i + 1) * per + k
			idx.append_array([a0, a0 + 1, b0, a0 + 1, b0 + 1, b0])
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = v
	arr[Mesh.ARRAY_TEX_UV] = uv
	arr[Mesh.ARRAY_NORMAL] = nrm
	arr[Mesh.ARRAY_INDEX] = idx
	var mesh := ArrayMesh.new()
	if land != null:
		var st := SurfaceTool.new()
		st.create_from_arrays(arr)
		st.generate_normals()
		mesh = st.commit()
	else:
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return mesh


## How far from the model's middle, along `d`, the field's fence (FIT: centre x, z, floor, long axis deg,
## half length, half width) lies, plus `margin`.
static func _past_fence(d: Vector3, fit: Array, margin: float) -> float:
	var a := deg_to_rad(float(fit[3]))
	var hl: float = float(fit[4]) + margin
	var hw: float = float(fit[5]) + margin
	var r := 0.0
	while r < 400.0:
		var x := d.x * r - float(fit[0])
		var z := d.z * r - float(fit[1])
		var rx := x * cos(a) + z * sin(a)
		var rz := -x * sin(a) + z * cos(a)
		if (rx / hl) * (rx / hl) + (rz / hw) * (rz / hw) > 1.0:
			return r
		r += 0.25
	return r
## A ground's own land model (SURROUNDS `land`): drawn like the painted map, taking no sun shadow
## (past the shadow map's reach the Mobile renderer would draw it in shade) and casting none.
static func _add_land(root: Node3D, s: Dictionary, dir: String) -> void:
	for key in ["land", "far_land"]:
		if s.has(key):
			_add_land_model(root, dir + str(s[key]), "Land" if key == "land" else "FarLand")
	if not s.has("trees") or not FileAccess.file_exists(dir + str(s["trees"])):
		return
	var buf := FileAccess.get_file_as_bytes(dir + str(s["trees"])).to_float32_array()
	var gums := load_glb(dir + str(s["gums"])) if s.has("gums") else null
	if gums == null:
		_add_trees(root, buf, float(s["y"]), 6 if s.get("trees_y", false) else 5)
		return
	_paint_vertex_colours(gums)
	# like the land, the trees take no shadow: past the sun's shadow range they would read as in shade
	for mi: MeshInstance3D in gums.find_children("*", "MeshInstance3D", true, false):
		for i in mi.mesh.get_surface_count():
			var m := mi.mesh.surface_get_material(i) as BaseMaterial3D
			if m != null:
				m.disable_receive_shadows = true
	_add_gums(root, buf, gums)
	gums.free()


## One model of the land (its colours in its vertices), casting and taking no shadow.
static func _add_land_model(root: Node3D, path: String, node_name: String) -> void:
	var land := load_glb(path)
	if land != null:
		land.name = node_name
		_paint_vertex_colours(land)
		for mi: MeshInstance3D in land.find_children("*", "MeshInstance3D", true, false):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mi.set_meta("open_ground", true)
			if mi.mesh == null:
				continue
			for i in mi.mesh.get_surface_count():
				var m := mi.get_active_material(i) as StandardMaterial3D
				if m != null:
					var own := m.duplicate() as StandardMaterial3D
					own.disable_receive_shadows = true
					mi.set_surface_override_material(i, own)
		root.add_child(land)


## How far the match camera sees at the ground `slug`: 900 m, or further where the ground's land
## carries its far country (SURROUNDS `far`, as at Barossa Park, whose ranges stand 3 to 10 km off).
static func view_far(slug: String) -> float:
	return float(SURROUNDS.get(slug, {}).get("far", 900.0))


## Trees nearer the camera than this draw as a whole gum (trunk, limbs and leaf clumps), further ones as the
## gum's coarse crown.
const GUM_NEAR := 450.0


## The land's trees from the ground's own gum models (`gums`: nodes gum<k>_leaf, gum<k>_wood and gum<k>_far, each
## at 1 m tall and 1 m crown radius), one batch a variant a block, each tree its own height, crown, turn and shade.
## Records are x, ground y, z, height, crown radius, shade (model metres).
static func _add_gums(root: Node3D, buf: PackedFloat32Array, gums: Node3D) -> void:
	var meshes := {}
	for mi: MeshInstance3D in gums.find_children("gum*", "MeshInstance3D", true, false):
		meshes[str(mi.name)] = mi.mesh
	var kinds := 0
	while meshes.has("gum%d_leaf" % kinds):
		kinds += 1
	if kinds == 0:
		return
	var blocks := {}
	for i in range(0, buf.size() - 5, 6):
		var key := Vector3i(floori(buf[i] / TREE_BLOCK), floori(buf[i + 2] / TREE_BLOCK),
				int(fposmod(buf[i + 5] * 7919.0, 1.0) * kinds) % kinds)
		if not blocks.has(key):
			blocks[key] = []
		blocks[key].append(i)
	for key: Vector3i in blocks:
		var ids: Array = blocks[key]
		var parts := [["gum%d_leaf" % key.z, true, 0.0, GUM_NEAR], ["gum%d_wood" % key.z, false, 0.0, GUM_NEAR],
				["gum%d_far" % key.z, true, GUM_NEAR, 0.0]]
		for part: Array in parts:
			if not meshes.has(part[0]):
				continue
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.use_colors = true
			mm.mesh = meshes[part[0]]
			mm.instance_count = ids.size()
			for j in ids.size():
				var i: int = ids[j]
				var h: float = buf[i + 3]
				var r: float = buf[i + 4]
				var shade: float = buf[i + 5]
				var turn := Basis(Vector3.UP, fposmod(shade * 113.7, 1.0) * TAU)
				mm.set_instance_transform(j, Transform3D(turn.scaled(Vector3(r, h, r)), Vector3(buf[i], buf[i + 1], buf[i + 2])))
				# grey-green blue gum to the darker river red gum, tree to tree
				var c := Color(0.92, 0.96, 0.93).lerp(Color(1.06, 1.04, 0.9), shade) * (0.85 + 0.3 * fposmod(shade * 7.3, 1.0))
				mm.set_instance_color(j, c if part[1] else Color.WHITE)
			var mi := MultiMeshInstance3D.new()
			mi.name = "%s_%d_%d" % [part[0], key.x, key.y]
			mi.multimesh = mm
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mi.visibility_range_begin = part[2]
			mi.visibility_range_end = part[3]
			mi.visibility_range_begin_margin = 20.0 if part[2] > 0.0 else 0.0
			mi.visibility_range_end_margin = 20.0 if part[3] > 0.0 else 0.0
			mi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
			root.add_child(mi)


## The ring's radii, m from the model's middle (0 is `inner`): close rings keep the painted map's
## roads straight where it is seen, the last runs out past the horizon.
const RINGS := [0.0, 250.0, 400.0, 600.0, 850.0, 1100.0]
## On real land: a ring every LAND_STEP m for the first 300 m (the data's own 5 m), 15 m to 900 m
## and 50 m past it; the ring banks from the model's street up to the real land over LAND_BANK m.
const LAND_STEP := 5.0
const LAND_BANK := 20.0


## Land with `relief`: RELIEF_SIDES spokes and a ring every RELIEF_RING m (twice that past 600 m) out to
## RELIEF_REACH, so the ground follows the land's rise and fall to within its grid (about 15 m at 600 m).
const RELIEF_SIDES := 256
const RELIEF_RING := 10.0
const RELIEF_REACH := 1100.0


## The land's height over the model's floor at x, z (model metres) from a relief buffer: its side n and
## span m, then n x n heights row by row from the north-west corner (z rows, x columns), bilinear between
## them, the edge's height past it. Written by each ground's relief.py (tools/grounds/scg/relief.py).
static func relief_at(rel: PackedFloat32Array, x: float, z: float) -> float:
	var n := int(rel[0])
	var span := rel[1]
	var fx := clampf((x / span + 0.5) * (n - 1), 0.0, n - 1.001)
	var fz := clampf((z / span + 0.5) * (n - 1), 0.0, n - 1.001)
	var ix := int(fx)
	var iz := int(fz)
	var tx := fx - ix
	var tz := fz - iz
	var a := rel[2 + iz * n + ix]
	var b := rel[2 + iz * n + ix + 1]
	var c := rel[2 + (iz + 1) * n + ix]
	var d := rel[2 + (iz + 1) * n + ix + 1]
	return lerpf(lerpf(a, b, tx), lerpf(c, d, tx), tz)
## Trees are drawn in square blocks this many metres a side, so the camera draws only those in view.
const TREE_BLOCK := 250.0
## Past this many metres from a tree block's middle a ground with "tree_lod" draws its crowns plain (_canopy_far_mesh).
const TREE_NEAR := 320.0


## Every tree of the map (x, z, height, canopy radius, shade; model metres) as a trunk and a rounded
## canopy, one batch a block of the park. Unlit by their own shadows (the map paints their shade).
## deep: a broad tree's crown hangs down to a few metres off the ground (eucalypts seen from the side in
## Google Earth: one deep mass, not a ball on a bare trunk); it stays as wide as measured.
static func _add_trees(root: Node3D, buf: PackedFloat32Array, y: float, stride := 5, kind := "", deep := false,
		lod := false, relief := PackedFloat32Array(), land: GroundTerrain = null, reach := INF) -> void:
	var gum := kind == "gum"
	var canopy := _gum_canopy_mesh() if gum else _canopy_mesh()
	var trunk := CylinderMesh.new()
	trunk.top_radius = 0.022
	trunk.bottom_radius = 0.035
	trunk.height = 1.0
	trunk.radial_segments = 8
	trunk.rings = 0
	trunk.cap_top = false
	trunk.cap_bottom = false
	var leaf := StandardMaterial3D.new()
	leaf.resource_name = "tree_leaf"
	leaf.vertex_color_use_as_albedo = true
	# A gum's colours are on its vertices (olive leaves, pale limbs); the instance colour shades it.
	leaf.albedo_color = Color(1, 1, 1) if gum else Color(0.27, 0.34, 0.19)
	leaf.vertex_color_is_srgb = gum
	leaf.roughness = 1.0
	leaf.disable_receive_shadows = true
	var bark := StandardMaterial3D.new()
	bark.resource_name = "tree_bark"
	# River red gum and sugar gum bark in Google Earth's Kardinia Park: pale grey, not brown.
	bark.albedo_color = Color(0.6, 0.57, 0.52) if gum else Color(0.33, 0.29, 0.24)
	bark.roughness = 1.0
	bark.disable_receive_shadows = true
	var blocks := {}
	# Each tree's x, z (and its own ground height when stride is 6) begin its record.
	var zo := 2 if stride == 6 else 1
	var o := 1 if stride == 6 else 0
	for i in range(0, buf.size() - stride + 1, stride):
		if Vector2(buf[i], buf[i + zo]).length() > reach:
			continue
		var key := Vector2i(floori(buf[i] / TREE_BLOCK), floori(buf[i + zo] / TREE_BLOCK))
		if not blocks.has(key):
			blocks[key] = []
		blocks[key].append(i)
	for key: Vector2i in blocks:
		var ids: Array = blocks[key]
		var leaves := MultiMesh.new()
		leaves.transform_format = MultiMesh.TRANSFORM_3D
		leaves.use_colors = true
		leaves.mesh = canopy
		leaves.instance_count = ids.size()
		var stems := MultiMesh.new()
		stems.transform_format = MultiMesh.TRANSFORM_3D
		stems.mesh = trunk
		stems.instance_count = ids.size()
		for j in ids.size():
			var i: int = ids[j]
			var h: float = buf[i + 2 + o]
			var r: float = buf[i + 3 + o]
			var ground_y := y if land == null else land.height(buf[i], buf[i + zo]) - 0.1
			var at := Vector3(buf[i], buf[i + 1] if stride == 6 else ground_y, buf[i + zo])
			if not relief.is_empty():
				at.y += relief_at(relief, at.x, at.z)
			var turn := Basis(Vector3.UP, buf[i + 4 + o] * TAU)
			var crown := h - r * (0.75 if gum else 1.1)
			var squash := 0.7 if gum else 0.85
			var shade: float = buf[i + 4 + o]
			if shade >= 2.0:
				# A pine or cypress (shade 2 and up, from a ground's measured canopy heights): one tall dark
				# column from low on the trunk to the top, not a ball on a stick.
				shade -= 2.0
				var half := h * 0.42
				crown = h - half * 0.95
				leaves.set_instance_transform(j, Transform3D(turn.scaled(Vector3(r, half, r)), at + Vector3(0, crown, 0)))
				leaves.set_instance_color(j, Color(0.62, 0.72, 0.62) * (0.85 + 0.3 * fposmod(shade * 7.3, 1.0)))
			else:
				var half := r * squash
				# A tree listed more than four times as tall as its crown is wide (Harbour Esplanade's
				# slim street trees, Google Earth ge_ferry_b) gets a narrow upright crown.
				if h > r * 4.0:
					half = h * 0.34
					crown = h - half
				if deep:
					half = maxf(half, 0.5 * (h - clampf(0.25 * h, 2.0, 4.0)))
					crown = h - half
				leaves.set_instance_transform(j, Transform3D(turn.scaled(Vector3(r, half, r)), at + Vector3(0, crown, 0)))
				# Eucalypt grey-green to elm green, a little lighter or darker tree to tree.
				leaves.set_instance_color(j, Color(0.92, 0.95, 0.9).lerp(Color(1.1, 1.08, 0.95), shade) * (0.85 + 0.3 * fposmod(shade * 7.3, 1.0)))
			stems.set_instance_transform(j, Transform3D(Basis().scaled(Vector3(h, crown, h)), at + Vector3(0, crown * 0.5, 0)))
		var sets := [[leaves, leaf, "Trees", 0.0, 0.0], [stems, bark, "Trunks", 0.0, 0.0]]
		if lod:
			# A ground whose trees fill Google Earth's canopy crown by crown (Bellerive: 13,000) draws a block
			# whose middle is past TREE_NEAR m in one ball a crown and no trunks, about a sixth of the triangles.
			var far := MultiMesh.new()
			far.transform_format = MultiMesh.TRANSFORM_3D
			far.use_colors = true
			far.mesh = _canopy_far_mesh()
			far.instance_count = ids.size()
			far.buffer = leaves.buffer
			sets = [[leaves, leaf, "Trees", 0.0, TREE_NEAR], [stems, bark, "Trunks", 0.0, TREE_NEAR],
					[far, leaf, "TreesFar", TREE_NEAR, 0.0]]
		for tree_set: Array in sets:
			var mi := MultiMeshInstance3D.new()
			mi.name = "%s_%d_%d" % [tree_set[2], key.x, key.y]
			mi.multimesh = tree_set[0]
			mi.material_override = tree_set[1]
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mi.visibility_range_begin = tree_set[3]
			mi.visibility_range_end = tree_set[4]
			root.add_child(mi)


## The map's buildings round the ground (point count, height, then the footprint's x, z): plain
## walls in a pale render or brick and a flat roof each, as one mesh. Seen past the stands and
## from a fly-through, they set the MCG in its city rather than on a plain. `style` "towers" draws a
## city of glass and concrete instead (Docklands, _add_towers). With `land` each stands on the real land.
## `facade_r` (SURROUNDS "facades", m from the model's middle): buildings that near are modelled
## closer (_facade): a block of flats or offices gets its floors, every window a real recess with
## its sill, head and reveals (no windows painted on), and a house its hipped roof. They are a mesh
## of their own ("facade_detail"); Low swaps in their plain walls ("facade_plain", Oval3DQuality).
static func _add_buildings(root: Node3D, buf: PackedFloat32Array, y0: float, walls: Array = [],
		roofs: Array = [], roof_rgb := PackedFloat32Array(), tint := Color.WHITE,
		colours := PackedByteArray(), facade_r := 0.0, style := "", land: GroundTerrain = null, reach := INF) -> void:
	if style == "towers":
		_add_towers(root, buf, y0, tint, style, land)
		return
	var far := _geo()
	var near := _geo()
	var near_plain := _geo()
	# Houses (a negative height: GMHBA's, Bellerive's) are drawn into these, then join the far mesh.
	var v := PackedVector3Array()
	var nrm := PackedVector3Array()
	var col := PackedColorArray()
	var uv := PackedVector2Array()
	var towers := style == "towers"
	const WALLS := [Color(0.86, 0.84, 0.8), Color(0.78, 0.76, 0.72), Color(0.72, 0.6, 0.5), Color(0.9, 0.88, 0.84),
			Color(0.66, 0.66, 0.66)]
	# Google Earth's Docklands: blue-grey and green-grey glass, pale and mid concrete, a little brick.
	# Round 12 self-check (obl_s): with more of the towers glass, the darkest glass read navy where Google Earth's north
	# towers are mid grey; the palette's floor raised.
	const GLASS := [Color8(84, 100, 114), Color8(76, 92, 106), Color8(96, 110, 120), Color8(70, 84, 98),
			Color8(104, 116, 126), Color8(80, 96, 100)]
	# Marvel round 12 (own audit of the round 11 PC renders): the concrete towers read near-white with punched
	# windows from every side (ext_180, obl_s, obl_se, obl_e), where Google Earth's read mid grey-blue: darker
	# concrete, and more of the towers glass.
	const CONCRETE := [Color8(150, 152, 150), Color8(132, 134, 134), Color8(160, 158, 150), Color8(128, 118, 108),
			Color8(142, 148, 152), Color8(116, 120, 122)]
	var i := 0
	var b := 0
	while i + 1 < buf.size():
		# A record is n, height, then n points; or, for a stacked part of a building (Marvel: the City
		# of Melbourne's massing), -n, top, base, building id, then n points. One building's parts
		# share a look.
		var n := int(buf[i])
		var h: float = buf[i + 1]
		var head := 2
		if n < 0:   # a stacked part: only the towers draw its base (_add_towers)
			n = -n
			head = 4
		# A negative height is a house: walls to the eaves at -h, then a hipped roof (GMHBA's Geelong).
		# At -100 and below it is a gable-roofed house with its eaves at -h - 100 (Bellerive's, read off
		# Google Earth: tools/grounds/bellerive/houses_ge.py).
		var gable := h <= -100.0
		if gable:
			h += 100.0
		var hipped := h < 0.0
		h = absf(h)
		var foot := PackedVector2Array()
		for k in n:
			foot.append(Vector2(buf[i + head + k * 2], buf[i + head + 1 + k * 2]))
		i += head + n * 2
		b += 1
		if reach < INF:   # past the ring's end the background scene draws the town (b is kept: colours stay in step)
			var c := Vector2.ZERO
			for q in foot:
				c += q
			if (c / maxf(foot.size(), 1)).length() > reach:
				continue
		# On real land the ground floor sits at the lowest land under it (dug in on the high side).
		var y := y0 if land == null else land.base(foot) - 0.1
		var wall: Color = walls[b % walls.size()] if not walls.is_empty() else WALLS[b % WALLS.size()]
		var roof := wall.darkened(0.18)
		if hipped:
			var hr: Array = roofs if not roofs.is_empty() else HOUSE_ROOFS
			roof = hr[(b * 7) % hr.size()]
		# A ground that lists each roof's own colour from above (SURROUNDS "roof_colours", linear RGB).
		if roof_rgb.size() >= b * 3:
			roof = Color(roof_rgb[b * 3 - 3], roof_rgb[b * 3 - 2], roof_rgb[b * 3 - 1])
		if colours.size() >= b * 6:
			var o := (b - 1) * 6
			wall = Color8(colours[o], colours[o + 1], colours[o + 2])
			roof = Color8(colours[o + 3], colours[o + 4], colours[o + 5])
		if hipped:
			# Walls face out whichever way round the footprint was drawn.
			var ccw := 0.0
			for k in n:
				ccw += foot[k].cross(foot[(k + 1) % n])
			for k in n:
				var a := foot[k]
				var c := foot[(k + 1) % n]
				var out := Vector3(c.y - a.y, 0.0, a.x - c.x).normalized() * (1.0 if ccw > 0.0 else -1.0)
				var shade := wall * (0.92 + 0.08 * absf(out.x))
				_front(v, nrm, col, Vector3(a.x, y, a.y), Vector3(c.x, y, c.y), Vector3(c.x, y + h, c.y), out, shade)
				_front(v, nrm, col, Vector3(a.x, y, a.y), Vector3(c.x, y + h, c.y), Vector3(a.x, y + h, a.y), out, shade)
				if hipped and foot[k].length() < HOUSE_DETAIL_R:
					_house_windows(a, c, y, out, v, nrm, col)
					if h > 5.0:                        # a two-storey house: the upper floor's windows too
						_house_windows(a, c, y + h - 3.0, out, v, nrm, col)
			# The roof oversails the walls by HOUSE_EAVE (a boxed eave, its soffit seen from the street).
			var cen := Vector2.ZERO
			for p in foot:
				cen += p
			cen /= foot.size()
			var eave := PackedVector2Array()
			for p in foot:
				var dd := (p - cen).length()
				eave.append(cen + (p - cen) * ((dd + HOUSE_EAVE) / maxf(dd, 0.01)))
			for k in n:
				var a := foot[k]
				var c := foot[(k + 1) % n]
				var ea := eave[k]
				var ec := eave[(k + 1) % n]
				var sof := wall.lightened(0.15) * 0.8
				sof.a = 1.0
				_front(v, nrm, col, Vector3(a.x, y + h, a.y), Vector3(ec.x, y + h, ec.y), Vector3(c.x, y + h, c.y), Vector3.DOWN, sof)
				_front(v, nrm, col, Vector3(a.x, y + h, a.y), Vector3(ea.x, y + h, ea.y), Vector3(ec.x, y + h, ec.y), Vector3.DOWN, sof)
			if gable:
				_gable_roof(eave, y + h, roof, wall, v, nrm, col)
			else:
				_hip_roof(eave, y + h, roof, v, nrm, col)
			if b % 3 == 0:                         # a brick chimney through the roof on one house in three
				var ch := cen + (foot[0] - cen) * 0.45
				_box(Vector3(ch.x, y + h, ch.y), Vector2(0.55, 0.75), 3.6, Color(0.55, 0.32, 0.26), v, nrm, col)
			continue
		var mid := Vector2.ZERO
		for p in foot:
			mid += p / float(n)
		if facade_r > 0.0 and mid.length() < facade_r:
			_plain_building(near_plain, foot, y, h, wall, roof)
			_facade(near, foot, y, h, wall, roof)
		else:
			_plain_building(far, foot, y, h, wall, roof)
	far["v"].append_array(v)
	far["n"].append_array(nrm)
	far["c"].append_array(col)
	_add_geo(root, far, "Buildings", tint, "")
	_add_geo(root, near, "BuildingsNear", tint, "facade_detail")
	_add_geo(root, near_plain, "BuildingsNearPlain", tint, "facade_plain").visible = false


static func _geo() -> Dictionary:
	return {"v": PackedVector3Array(), "n": PackedVector3Array(), "c": PackedColorArray()}


## One triangle, wound to face along `nrm` as _front does.
static func _tri(g: Dictionary, a: Vector3, b: Vector3, c: Vector3, nrm: Vector3, col: Color) -> void:
	if (c - a).cross(b - a).dot(nrm) < 0.0:
		var t := b
		b = c
		c = t
	for p: Vector3 in [a, b, c]:
		g["v"].append(p)
		g["n"].append(nrm)
		g["c"].append(col)


static func _quad(g: Dictionary, a: Vector3, b: Vector3, c: Vector3, d: Vector3, nrm: Vector3, col: Color) -> void:
	_tri(g, a, b, c, nrm, col)
	_tri(g, a, c, d, nrm, col)


## Which way is out from each wall, whichever way round the footprint was drawn.
static func _outward(foot: PackedVector2Array) -> float:
	var ccw := 0.0
	for k in foot.size():
		ccw += foot[k].cross(foot[(k + 1) % foot.size()])
	return 1.0 if ccw > 0.0 else -1.0


static func _plain_building(g: Dictionary, foot: PackedVector2Array, y: float, h: float, wall: Color,
		roof: Color) -> void:
	var n := foot.size()
	var sgn := _outward(foot)
	for k in n:
		var a := foot[k]
		var c := foot[(k + 1) % n]
		var out := Vector3(c.y - a.y, 0.0, a.x - c.x).normalized() * sgn
		_quad(g, Vector3(a.x, y, a.y), Vector3(c.x, y, c.y), Vector3(c.x, y + h, c.y), Vector3(a.x, y + h, a.y),
				out, wall * (0.92 + 0.08 * absf(out.x)))
	var tri := Geometry2D.triangulate_polygon(foot)
	for k in range(0, tri.size(), 3):
		_tri(g, Vector3(foot[tri[k]].x, y + h, foot[tri[k]].y), Vector3(foot[tri[k + 1]].x, y + h, foot[tri[k + 1]].y),
				Vector3(foot[tri[k + 2]].x, y + h, foot[tri[k + 2]].y), Vector3.UP, roof)


const FLOOR_H := 3.3      # a storey
const SILL := 1.0         # wall below each window band
const RECESS := 0.35      # how deep the glass sits behind the wall
const PIER := 0.9         # wall kept at each end of a wall's window band
const GLASS := Color(0.2, 0.24, 0.29)
const MULLION := Color(0.3, 0.31, 0.33)


## One building near the ground, modelled: a house (low, small, near enough a rectangle) gets a
## hipped roof over its walls; anything of three storeys or more gets its floors and recessed
## window bands; a lower shop or works building its glazed street floor; a shed under 3.5 m stays plain.
static func _facade(g: Dictionary, foot: PackedVector2Array, y: float, h: float, wall: Color, roof: Color) -> void:
	var n := foot.size()
	var area := _area(foot)
	if h <= 9.0 and area < 400.0:
		var rect := _min_rect(foot)
		if not rect.is_empty() and area / float(rect["area"]) > 0.8:
			var short: float = minf(rect["w"], rect["l"])
			var ridge := clampf(short * 0.28, 1.2, 3.2)
			var eave := maxf(h - ridge, 2.8)
			_plain_walls(g, foot, y, eave, wall)
			_rect_hip_roof(g, rect, y + eave, y + eave + ridge, roof)
			return
	if h < 3.5:
		_plain_building(g, foot, y, h, wall, roof)
		return
	# A low shop or works building (under three storeys, not a house): its street floor glazed, recessed like the
	# flats' bands, the wall above plain to the roof.
	var shop := h < 9.0
	var floors := 1 if shop else maxi(int(round(h / FLOOR_H)), 1)
	var fh := h / float(floors)
	var sgn := _outward(foot)
	var shade_in := wall.darkened(0.3)
	for k in n:
		var a := foot[k]
		var c := foot[(k + 1) % n]
		var el := a.distance_to(c)
		var out := Vector3(c.y - a.y, 0.0, a.x - c.x).normalized() * sgn
		var col := wall * (0.92 + 0.08 * absf(out.x))
		var A := Vector3(a.x, 0.0, a.y)
		var C := Vector3(c.x, 0.0, c.y)
		if el < 2.0 * PIER + 1.5:
			_quad(g, A + Vector3.UP * y, C + Vector3.UP * y, C + Vector3.UP * (y + h), A + Vector3.UP * (y + h), out, col)
			continue
		var L := A.lerp(C, PIER / el)
		var R := C.lerp(A, PIER / el)
		var dn := -out * RECESS
		for f in floors:
			var z0 := y + f * fh
			var zs := z0 + (0.5 if shop else SILL)
			var zh := (y + minf(2.9, h - 0.8)) if shop else z0 + fh - (0.35 if f == floors - 1 else 0.0)
			var z1 := z0 + fh
			var up := Vector3.UP
			# the wall: below the band, the two piers, and above the band on the top floor
			_quad(g, A + up * z0, C + up * z0, C + up * zs, A + up * zs, out, col)
			_quad(g, A + up * zs, L + up * zs, L + up * zh, A + up * zh, out, col)
			_quad(g, R + up * zs, C + up * zs, C + up * zh, R + up * zh, out, col)
			if zh < z1:
				_quad(g, A + up * zh, C + up * zh, C + up * z1, A + up * z1, out, col)
			# the glass, set back, and the recess's four sides
			_quad(g, L + dn + up * zs, R + dn + up * zs, R + dn + up * zh, L + dn + up * zh, out, GLASS)
			_quad(g, L + up * zs, R + up * zs, R + dn + up * zs, L + dn + up * zs, Vector3.UP, col)
			_quad(g, L + up * zh, R + up * zh, R + dn + up * zh, L + dn + up * zh, Vector3.DOWN, shade_in)
			var side := (C - A).normalized()
			_quad(g, L + up * zs, L + dn + up * zs, L + dn + up * zh, L + up * zh, side, shade_in)
			_quad(g, R + up * zs, R + dn + up * zs, R + dn + up * zh, R + up * zh, -side, shade_in)
			# mullions standing 0.14 m off the glass: every 1.6 m on a shopfront, every 2.4 m on a window band
			var span := L.distance_to(R)
			var nm := int(span / (1.6 if shop else 2.4))
			for m in range(1, nm + 1):
				var mc := L.lerp(R, float(m) / float(nm + 1))
				var w := side * 0.05
				var mf := dn * 0.6
				_quad(g, mc - w + mf + up * zs, mc + w + mf + up * zs, mc + w + mf + up * zh, mc - w + mf + up * zh, out, MULLION)
				_quad(g, mc - w + dn + up * zs, mc - w + mf + up * zs, mc - w + mf + up * zh, mc - w + dn + up * zh, -side, MULLION)
				_quad(g, mc + w + mf + up * zs, mc + w + dn + up * zs, mc + w + dn + up * zh, mc + w + mf + up * zh, side, MULLION)
	var tri := Geometry2D.triangulate_polygon(foot)
	for k in range(0, tri.size(), 3):
		_tri(g, Vector3(foot[tri[k]].x, y + h, foot[tri[k]].y), Vector3(foot[tri[k + 1]].x, y + h, foot[tri[k + 1]].y),
				Vector3(foot[tri[k + 2]].x, y + h, foot[tri[k + 2]].y), Vector3.UP, roof)


static func _plain_walls(g: Dictionary, foot: PackedVector2Array, y: float, h: float, wall: Color) -> void:
	var sgn := _outward(foot)
	for k in foot.size():
		var a := foot[k]
		var c := foot[(k + 1) % foot.size()]
		var out := Vector3(c.y - a.y, 0.0, a.x - c.x).normalized() * sgn
		_quad(g, Vector3(a.x, y, a.y), Vector3(c.x, y, c.y), Vector3(c.x, y + h, c.y), Vector3(a.x, y + h, a.y),
				out, wall * (0.92 + 0.08 * absf(out.x)))


static func _area(foot: PackedVector2Array) -> float:
	var s := 0.0
	for k in foot.size():
		s += foot[k].cross(foot[(k + 1) % foot.size()])
	return absf(s) * 0.5


## The smallest rectangle round the footprint lined up with one of its walls: its middle, long
## axis (unit), half length and half width; empty if the footprint is degenerate.
static func _min_rect(foot: PackedVector2Array) -> Dictionary:
	var best := {}
	for k in foot.size():
		var e := foot[(k + 1) % foot.size()] - foot[k]
		if e.length() < 0.5:
			continue
		var u := e.normalized()
		var v := Vector2(-u.y, u.x)
		var lo := Vector2(INF, INF)
		var hi := Vector2(-INF, -INF)
		for p in foot:
			var q := Vector2(p.dot(u), p.dot(v))
			lo = lo.min(q)
			hi = hi.max(q)
		var a := (hi.x - lo.x) * (hi.y - lo.y)
		if best.is_empty() or a < float(best["area"]):
			var m := (lo + hi) * 0.5
			best = {"area": a, "mid": u * m.x + v * m.y, "u": u, "v": v, "l": hi.x - lo.x, "w": hi.y - lo.y}
	if not best.is_empty() and float(best["area"]) < 1.0:
		return {}
	return best


## A hipped roof over the rectangle, 0.4 m of eave all round: a ridge along the long side, four
## slopes (two trapezoids, two triangles).
static func _rect_hip_roof(g: Dictionary, rect: Dictionary, z_eave: float, z_ridge: float, col: Color) -> void:
	var u: Vector2 = rect["u"]
	var v: Vector2 = rect["v"]
	var hl: float = rect["l"] * 0.5 + 0.4
	var hw: float = rect["w"] * 0.5 + 0.4
	if hw > hl:
		var t := u
		u = v
		v = -t
		var th := hl
		hl = hw
		hw = th
	var m: Vector2 = rect["mid"]
	var r := maxf(hl - hw, 0.0)
	var c00 := m - u * hl - v * hw
	var c10 := m + u * hl - v * hw
	var c11 := m + u * hl + v * hw
	var c01 := m - u * hl + v * hw
	var p0 := m - u * r
	var p1 := m + u * r
	var E := func(p: Vector2) -> Vector3: return Vector3(p.x, z_eave, p.y)
	var Rg := func(p: Vector2) -> Vector3: return Vector3(p.x, z_ridge, p.y)
	var dz := z_ridge - z_eave
	var nside := func(d: Vector2) -> Vector3: return Vector3(d.x * dz, hw, d.y * dz).normalized()
	_quad(g, E.call(c00), E.call(c10), Rg.call(p1), Rg.call(p0), nside.call(-v), col * 0.92)
	_quad(g, E.call(c11), E.call(c01), Rg.call(p0), Rg.call(p1), nside.call(v), col)
	_tri(g, E.call(c10), E.call(c11), Rg.call(p1), nside.call(u), col * 0.96)
	_tri(g, E.call(c01), E.call(c00), Rg.call(p0), nside.call(-u), col * 0.96)


static func _add_geo(root: Node3D, g: Dictionary, name: String, tint: Color, meta: String) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.name = name
	if (g["v"] as PackedVector3Array).is_empty():
		return mi
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = g["v"]
	arr[Mesh.ARRAY_NORMAL] = g["n"]
	arr[Mesh.ARRAY_COLOR] = g["c"]
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var mat := StandardMaterial3D.new()
	mat.resource_name = "city"
	mat.vertex_color_use_as_albedo = true
	mat.albedo_color = tint
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.roughness = 0.95
	mat.disable_receive_shadows = true
	mi.mesh = mesh
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.set_meta("open_ground", true)
	if meta != "":
		mi.set_meta(meta, true)
	root.add_child(mi)
	return mi


## One triangle wound so its front face looks along `n` (Godot draws clockwise faces as the front).
## The town's mesh is drawn from both sides, and a back face is lit with its normal turned round:
## roofs wound the other way were lit from under the ground (the grass's green bounce), walls from
## inside (sky blue only).
static func _front(v: PackedVector3Array, nrm: PackedVector3Array, col: PackedColorArray, a: Vector3, b: Vector3,
		c: Vector3, n: Vector3, colour: Color) -> void:
	if (c - a).cross(b - a).dot(n) < 0.0:
		var t := b
		b = c
		c = t
	v.append_array([a, b, c])
	nrm.append_array([n, n, n])
	col.append_array([colour, colour, colour])


## House detail (GMHBA's and Bellerive's suburbs): eaves past the walls everywhere, and within
## HOUSE_DETAIL_R of the ground windows stood on the walls as frames with a dark pane, modelled, so the
## houses read as houses from the stands' upper rows and the blimp. Past that a window is under a pixel.
const HOUSE_EAVE := 0.45
const HOUSE_DETAIL_R := 450.0


## Windows along one house wall from a to c (outward normal `out`): 1.0 m wide, 1.3 m tall on a 0.9 m
## sill, every 3.4 m or so, each a white frame standing 6 cm off the wall round a dark glass pane.
static func _house_windows(a: Vector2, c: Vector2, y: float, out: Vector3, v: PackedVector3Array,
		nrm: PackedVector3Array, col: PackedColorArray) -> void:
	var L := (c - a).length()
	if L < 2.6:
		return
	var n := maxi(1, int(L / 3.4))
	var dir := (c - a) / L
	var o2 := Vector2(out.x, out.z)
	var frame := Color(0.92, 0.92, 0.9)
	var glass := Color(0.16, 0.19, 0.22)
	for k in n:
		var m := a + dir * (L * (k + 0.5) / n)
		var P := func(u: float, z: float, d: float) -> Vector3:
			var q: Vector2 = m + dir * u + o2 * d
			return Vector3(q.x, y + z, q.y)
		var hw := 0.5
		var z0 := 0.9
		var z1 := 2.2
		var t := 0.09
		_front(v, nrm, col, P.call(-hw, z0, 0.03), P.call(hw, z0, 0.03), P.call(hw, z1, 0.03), out, glass)
		_front(v, nrm, col, P.call(-hw, z0, 0.03), P.call(hw, z1, 0.03), P.call(-hw, z1, 0.03), out, glass)
		# The frame: four bars, each a front face and its outer edge, 6 cm proud.
		for bar: Array in [[-hw - t, hw + t, z0 - t, z0], [-hw - t, hw + t, z1, z1 + t], [-hw - t, -hw, z0, z1], [hw, hw + t, z0, z1]]:
			var u0: float = bar[0]
			var u1: float = bar[1]
			var b0: float = bar[2]
			var b1: float = bar[3]
			_front(v, nrm, col, P.call(u0, b0, 0.06), P.call(u1, b0, 0.06), P.call(u1, b1, 0.06), out, frame)
			_front(v, nrm, col, P.call(u0, b0, 0.06), P.call(u1, b1, 0.06), P.call(u0, b1, 0.06), out, frame)
		var sill_up := Vector3.UP
		_front(v, nrm, col, P.call(-hw - t, z0 - t, 0.0), P.call(hw + t, z0 - t, 0.0), P.call(hw + t, z0 - t, 0.08), sill_up, frame)
		_front(v, nrm, col, P.call(-hw - t, z0 - t, 0.0), P.call(hw + t, z0 - t, 0.08), P.call(-hw - t, z0 - t, 0.08), sill_up, frame)


## A box standing at `base` (centre of its foot), `size` x and z, `h` tall: four walls and a top.
static func _box(base: Vector3, size: Vector2, h: float, colour: Color, v: PackedVector3Array,
		nrm: PackedVector3Array, col: PackedColorArray) -> void:
	var hx := size.x * 0.5
	var hz := size.y * 0.5
	var c := [Vector3(-hx, 0, -hz), Vector3(hx, 0, -hz), Vector3(hx, 0, hz), Vector3(-hx, 0, hz)]
	for k in 4:
		var p0: Vector3 = base + c[k]
		var p1: Vector3 = base + c[(k + 1) % 4]
		var mid := (p0 + p1) * 0.5 - base
		var n := Vector3(mid.x, 0, mid.z).normalized()
		var sh := colour * (0.9 + 0.1 * absf(n.x))
		sh.a = 1.0
		_front(v, nrm, col, p0, p1, p1 + Vector3.UP * h, n, sh)
		_front(v, nrm, col, p0, p1 + Vector3.UP * h, p0 + Vector3.UP * h, n, sh)
	var t := Vector3.UP * h
	_front(v, nrm, col, base + c[0] + t, base + c[1] + t, base + c[2] + t, Vector3.UP, colour.darkened(0.3))
	_front(v, nrm, col, base + c[0] + t, base + c[2] + t, base + c[3] + t, Vector3.UP, colour.darkened(0.3))


## Geelong's house roofs from above in Google Earth: terracotta tile, charcoal and grey Colorbond, pale zinc.
const HOUSE_ROOFS := [Color(0.62, 0.36, 0.28), Color(0.34, 0.34, 0.35), Color(0.55, 0.55, 0.54),
		Color(0.7, 0.42, 0.32), Color(0.45, 0.46, 0.47), Color(0.74, 0.74, 0.72), Color(0.52, 0.3, 0.25)]


## A hipped roof over a house's footprint: each eave rises to a ridge along the footprint's long axis,
## 0.45 of the house's narrow half-width high (about a 24 degree pitch). Faces lit by their slope.
## A gable roof over `foot` (the eave line): the ridge runs the house's whole length along its longest
## wall, each long side slopes up to it, and each end is a vertical triangle of wall (the gable) under it.
## An edge that climbs to one point of the ridge is an end; any other edge is a slope.
static func _gable_roof(foot: PackedVector2Array, eave: float, roof: Color, wall: Color, v: PackedVector3Array,
		nrm: PackedVector3Array, col: PackedColorArray) -> void:
	var c := Vector2.ZERO
	for p in foot:
		c += p
	c /= foot.size()
	var ax := Vector2.RIGHT
	var best := 0.0
	for k in foot.size():
		var e := foot[(k + 1) % foot.size()] - foot[k]
		if e.length() > best:
			best = e.length()
			ax = e.normalized()
	var across := Vector2(-ax.y, ax.x)
	var lo_a := INF
	var hi_a := -INF
	var lo_b := INF
	var hi_b := -INF
	for p in foot:
		var q := p - c
		lo_a = minf(lo_a, q.dot(ax))
		hi_a = maxf(hi_a, q.dot(ax))
		lo_b = minf(lo_b, q.dot(across))
		hi_b = maxf(hi_b, q.dot(across))
	var half_w := (hi_b - lo_b) * 0.5
	var mid := c + across * (lo_b + hi_b) * 0.5
	var rise := minf(half_w * 0.45, 3.0)
	var top := eave + rise
	for k in foot.size():
		var a := foot[k]
		var b := foot[(k + 1) % foot.size()]
		var ra := mid + ax * clampf((a - mid).dot(ax), lo_a, hi_a)
		var rb := mid + ax * clampf((b - mid).dot(ax), lo_a, hi_a)
		var pa := Vector3(a.x, eave, a.y)
		var pb := Vector3(b.x, eave, b.y)
		if (ra - rb).length() < 0.3:
			# the gable end: a wall triangle up to the ridge, facing out
			var r := (ra + rb) * 0.5
			var o := Vector3(b.y - a.y, 0.0, a.x - b.x).normalized()
			if o.dot(Vector3(a.x - c.x, 0.0, a.y - c.y)) < 0.0:
				o = -o
			var sh := wall * (0.92 + 0.08 * absf(o.x))
			sh.a = 1.0
			_front(v, nrm, col, pa, pb, Vector3(r.x, top, r.y), o, sh)
			continue
		var qa := Vector3(ra.x, top, ra.y)
		var qb := Vector3(rb.x, top, rb.y)
		for t: Array in [[pa, pb, qb], [pa, qb, qa]]:
			var nn: Vector3 = (t[1] - t[0]).cross(t[2] - t[0]).normalized()
			if nn.y < 0.0:
				nn = -nn
			var lit := roof * (0.78 + 0.22 * clampf(nn.dot(Vector3(0.3, 0.9, -0.3).normalized()), 0.0, 1.0) / 0.95)
			lit.a = 1.0
			_front(v, nrm, col, t[0], t[1], t[2], nn, lit)


static func _hip_roof(foot: PackedVector2Array, eave: float, roof: Color, v: PackedVector3Array,
		nrm: PackedVector3Array, col: PackedColorArray) -> void:
	var c := Vector2.ZERO
	for p in foot:
		c += p
	c /= foot.size()
	# Long axis from the longest edge.
	var ax := Vector2.RIGHT
	var best := 0.0
	for k in foot.size():
		var e := foot[(k + 1) % foot.size()] - foot[k]
		if e.length() > best:
			best = e.length()
			ax = e.normalized()
	var across := Vector2(-ax.y, ax.x)
	var lo_a := INF
	var hi_a := -INF
	var lo_b := INF
	var hi_b := -INF
	for p in foot:
		var q := p - c
		lo_a = minf(lo_a, q.dot(ax))
		hi_a = maxf(hi_a, q.dot(ax))
		lo_b = minf(lo_b, q.dot(across))
		hi_b = maxf(hi_b, q.dot(across))
	var half_w := (hi_b - lo_b) * 0.5
	var mid := c + across * (lo_b + hi_b) * 0.5
	var rise := minf(half_w * 0.45, 3.0)
	var ridge_half := maxf(0.0, (hi_a - lo_a) * 0.5 - half_w)
	var amid := (lo_a + hi_a) * 0.5
	var r0 := mid + ax * (amid - ridge_half)
	var r1 := mid + ax * (amid + ridge_half)
	for k in foot.size():
		var a := foot[k]
		var b := foot[(k + 1) % foot.size()]
		# Each eave edge climbs to the nearer end of the ridge (a hip at the ends, a slope along the sides).
		var ra := r0 if (a - r0).length() <= (a - r1).length() else r1
		var rb := r0 if (b - r0).length() <= (b - r1).length() else r1
		var pa := Vector3(a.x, eave, a.y)
		var pb := Vector3(b.x, eave, b.y)
		var qa := Vector3(ra.x, eave + rise, ra.y)
		var qb := Vector3(rb.x, eave + rise, rb.y)
		var tris := [[pa, pb, qb]]
		if ra != rb:
			tris.append([pa, qb, qa])
		for t: Array in tris:
			var nn: Vector3 = (t[1] - t[0]).cross(t[2] - t[0]).normalized()
			if nn.y < 0.0:
				nn = -nn
			var lit := roof * (0.78 + 0.22 * clampf(nn.dot(Vector3(0.3, 0.9, -0.3).normalized()), 0.0, 1.0) / 0.95)
			lit.a = 1.0
			_front(v, nrm, col, t[0], t[1], t[2], nn, lit)


## Docklands' towers (SURROUNDS "building_style": "towers"): glass curtain walls with a mullion every
## 1.5 m and a slab at every floor, or concrete with rows of windows, from TOWER_SHADER.
static func _add_towers(root: Node3D, buf: PackedFloat32Array, y0: float, tint := Color.WHITE, style := "",
		land: GroundTerrain = null) -> void:
	var v := PackedVector3Array()
	var nrm := PackedVector3Array()
	var col := PackedColorArray()
	var uv := PackedVector2Array()
	var towers := style == "towers"
	const WALLS := [Color(0.86, 0.84, 0.8), Color(0.78, 0.76, 0.72), Color(0.72, 0.6, 0.5), Color(0.9, 0.88, 0.84),
			Color(0.66, 0.66, 0.66)]
	# Google Earth's Docklands: blue-grey and green-grey glass, pale and mid concrete, a little brick.
	# Round 12 self-check (obl_s): with more of the towers glass, the darkest glass read navy where Google Earth's north
	# towers are mid grey; the palette's floor raised.
	const TOWER_GLASS := [Color8(84, 100, 114), Color8(76, 92, 106), Color8(96, 110, 120), Color8(70, 84, 98),
			Color8(104, 116, 126), Color8(80, 96, 100)]
	# Marvel round 12 (own audit of the round 11 PC renders): the concrete towers read near-white with punched
	# windows from every side (ext_180, obl_s, obl_se, obl_e), where Google Earth's read mid grey-blue: darker
	# concrete, and more of the towers glass.
	const TOWER_CONCRETE := [Color8(150, 152, 150), Color8(132, 134, 134), Color8(160, 158, 150), Color8(128, 118, 108),
			Color8(142, 148, 152), Color8(116, 120, 122)]
	var i := 0
	var b := 0
	while i + 1 < buf.size():
		# A record is n, height, then n points; or, for a stacked part of a building (Marvel: the City
		# of Melbourne's massing), -n, top, base, building id, then n points. One building's parts
		# share a look.
		var n := int(buf[i])
		var h: float = buf[i + 1]
		var z0 := 0.0
		var head := 2
		var id := -1
		if n < 0:
			n = -n
			z0 = buf[i + 2]
			id = int(buf[i + 3])
			head = 4
		var foot := PackedVector2Array()
		for k in n:
			foot.append(Vector2(buf[i + head + k * 2], buf[i + head + 1 + k * 2]))
		i += head + n * 2
		b += 1
		# On real land the ground floor sits at the lowest land under it (dug in on the high side).
		var y := y0 if land == null else land.base(foot) - 0.1
		var wall: Color = WALLS[b % WALLS.size()]
		var roof := wall.darkened(0.18)
		if towers:
			# The same building gets the same look every match: its pick hangs on its own corner.
			var pick := absi(int(foot[0].x * 7.0) * 31 + int(foot[0].y * 3.0) * 17 + b) if id < 0 else id * 7919 % 100003
			var glassy := (pick % 100) < ((85 if h > 30.0 else 40) if id < 0 else 70)
			wall = TOWER_GLASS[pick % TOWER_GLASS.size()] if glassy else TOWER_CONCRETE[pick % TOWER_CONCRETE.size()]
			wall.a = 1.0 if glassy else 0.5
			roof = Color8(128, 128, 124) if glassy else wall.darkened(0.25)  # Google Earth's grey roofs (top view)
		# Walls face out whichever way round the footprint was drawn.
		var ccw := 0.0
		for k in n:
			ccw += foot[k].cross(foot[(k + 1) % n])
		var run := 0.0
		for k in n:
			var a := foot[k]
			var c := foot[(k + 1) % n]
			var out := Vector3(c.y - a.y, 0.0, a.x - c.x).normalized() * (1.0 if ccw > 0.0 else -1.0)
			var shade := wall * (0.92 + 0.08 * absf(out.x))
			shade.a = wall.a
			var side := a.distance_to(c)
			for q: Array in [[Vector3(a.x, y + z0, a.y), Vector2(run, z0)], [Vector3(c.x, y + z0, c.y), Vector2(run + side, z0)],
					[Vector3(c.x, y + h, c.y), Vector2(run + side, h)], [Vector3(a.x, y + z0, a.y), Vector2(run, z0)],
					[Vector3(c.x, y + h, c.y), Vector2(run + side, h)], [Vector3(a.x, y + h, a.y), Vector2(run, h)]]:
				v.append(q[0])
				nrm.append(out)
				col.append(shade)
				uv.append(q[1])
			run += side
		var tri := Geometry2D.triangulate_polygon(foot)
		for k in tri:
			v.append(Vector3(foot[k].x, y + h, foot[k].y))
			nrm.append(Vector3.UP)
			col.append(Color(roof, 0.0))
			uv.append(Vector2(0.0, -1.0))
	if v.is_empty():
		return
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = v
	arr[Mesh.ARRAY_NORMAL] = nrm
	arr[Mesh.ARRAY_COLOR] = col
	if towers:
		arr[Mesh.ARRAY_TEX_UV] = uv
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var mat: Material
	if towers:
		var sm := ShaderMaterial.new()
		sm.shader = _tower_shader()
		sm.set_shader_parameter("tint", tint)
		mat = sm
	else:
		var m := StandardMaterial3D.new()
		m.vertex_color_use_as_albedo = true
		m.albedo_color = tint
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
		m.roughness = 0.95
		m.disable_receive_shadows = true
		mat = m
	mat.resource_name = "city"
	var mi := MeshInstance3D.new()
	mi.name = "Buildings"
	mi.mesh = mesh
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.set_meta("open_ground", true)
	root.add_child(mi)


static var _tower_sh: Shader

## The towers' walls: UV is (metres round the footprint, metres up), COLOR.a picks the wall (1 glass
## curtain wall, 0.5 concrete with windows, 0 a roof). Past a few hundred metres the pattern fades to
## its own average colour, so it never shimmers.
static func _tower_shader() -> Shader:
	if _tower_sh == null:
		_tower_sh = Shader.new()
		_tower_sh.code = TOWER_SHADER
	return _tower_sh


const TOWER_SHADER := """
shader_type spatial;
render_mode cull_disabled, shadows_disabled;
uniform vec4 tint : source_color = vec4(1.0);

float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }

void fragment() {
	// The palette is written as sRGB colours (Color8); vertex colours reach the shader unconverted, so
	// without this the walls and roofs rendered far paler than the colours picked (2026-11-22: roofs
	// (92, 94, 96) rendered near white from above, against Google Earth's mid grey).
	vec3 c = COLOR.rgb;
	vec3 lin = mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c));
	vec3 base = lin * tint.rgb;
	float style = COLOR.a;
	if (style < 0.25) {
		ALBEDO = base;
		ROUGHNESS = 0.95;
	} else if (style > 0.75) {
		vec2 cell = vec2(UV.x / 1.5, UV.y / 3.4);
		vec2 f = fract(cell);
		vec2 w = fwidth(cell);
		float fade = clamp(1.6 - max(w.x, w.y) * 2.5, 0.0, 1.0);
		float h = hash(floor(cell));
		float frame = max(step(f.x, 0.07), step(f.y, 0.17));
		vec3 glass = base * (0.82 + 0.3 * h);
		vec3 detail = mix(glass, base * 1.45 + vec3(0.04), frame);
		vec3 avg = base * 1.08;
		ALBEDO = mix(avg, detail, fade);
		ROUGHNESS = mix(0.9, mix(0.3, 0.8, frame), fade);
		SPECULAR = 0.6;
	} else {
		vec2 cell = vec2(UV.x / 3.0, UV.y / 3.4);
		vec2 f = fract(cell);
		vec2 w = fwidth(cell);
		float fade = clamp(1.6 - max(w.x, w.y) * 2.5, 0.0, 1.0);
		float h = hash(floor(cell));
		float win = step(0.18, f.x) * step(f.x, 0.82) * step(0.3, f.y) * step(f.y, 0.86);
		vec3 pane = vec3(0.05, 0.07, 0.09) * (0.7 + 0.6 * h);
		vec3 detail = mix(base, pane, win);
		vec3 avg = mix(base, vec3(0.06, 0.08, 0.1), 0.36);
		ALBEDO = mix(avg, detail, fade);
		ROUGHNESS = 0.9;
	}
}
"""


## A canopy of about radius 1: two lumpy lobes, one high and one off to the side, so a park of them
## reads as gums and elms rather than balls on sticks.
## A far crown: one plain ball, 6 sides and 3 rings, flat underneath like _canopy_mesh's lobes.
static func _canopy_far_mesh() -> ArrayMesh:
	var sphere := SphereMesh.new()
	sphere.radius = 0.9
	sphere.height = 1.8
	sphere.radial_segments = 6
	sphere.rings = 3
	var arr := sphere.get_mesh_arrays()
	var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	for k in v.size():
		v[k] = Vector3(v[k].x, maxf(v[k].y, -0.45), v[k].z)
	arr[Mesh.ARRAY_VERTEX] = v
	arr[Mesh.ARRAY_TEX_UV] = null
	arr[Mesh.ARRAY_TANGENT] = null
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return mesh


## A canopy of about radius 1: two lumpy lobes, one high and one off to the side, so a park of them
## reads as gums and elms rather than balls on sticks.
## A eucalypt's crown, radius about 1 round its middle: open clumps of leaves on pale limbs, gaps between
## them (Google Earth's Kardinia Park gums are open and uneven, not one round ball). Colours on the vertices.
static func _gum_canopy_mesh() -> ArrayMesh:
	var sphere := SphereMesh.new()
	sphere.radius = 1.0
	sphere.height = 2.0
	sphere.radial_segments = 6
	sphere.rings = 3
	var src := sphere.get_mesh_arrays()
	var v := PackedVector3Array()
	var nrm := PackedVector3Array()
	var col := PackedColorArray()
	var idx := PackedInt32Array()
	var leaf := Color(0.3, 0.35, 0.22)
	var limb := Color(0.55, 0.52, 0.47)
	# Clumps: position in the crown and radius. Spread wide and flat-topped, as a gum is.
	var clumps := [[Vector3(0.0, 0.35, 0.05), 0.42], [Vector3(0.55, 0.15, 0.25), 0.38], [Vector3(-0.5, 0.2, -0.3), 0.4],
			[Vector3(0.2, -0.05, -0.62), 0.33], [Vector3(-0.3, -0.1, 0.6), 0.34], [Vector3(0.7, -0.2, -0.35), 0.28],
			[Vector3(-0.72, -0.25, 0.2), 0.3], [Vector3(0.15, 0.6, -0.25), 0.3]]
	for c: Array in clumps:
		var at: Vector3 = c[0]
		var r: float = c[1]
		var base := v.size()
		for k in (src[Mesh.ARRAY_VERTEX] as PackedVector3Array).size():
			var p: Vector3 = src[Mesh.ARRAY_VERTEX][k]
			var bump := 1.0 + 0.25 * sin(p.x * 6.3 + p.y * 4.1 + at.z * 7.0) * cos(p.z * 5.2 - p.y * 3.3 + at.x * 5.0)
			v.append(at + Vector3(p.x, p.y * 0.75, p.z) * r * bump)
			nrm.append(src[Mesh.ARRAY_NORMAL][k])
			# The clump's underside a little darker.
			col.append(leaf * (0.8 + 0.2 * clampf(p.y + 0.5, 0.0, 1.0)))
		for k in (src[Mesh.ARRAY_INDEX] as PackedInt32Array):
			idx.append(base + k)
		# A limb from the top of the trunk (the crown's base, 0.75 below its middle) out to the clump.
		var a := Vector3(0.0, -0.75, 0.0)
		var b := at - Vector3(0.0, r * 0.4, 0.0)
		var ax := (b - a).normalized()
		var u := ax.cross(Vector3.FORWARD if absf(ax.dot(Vector3.FORWARD)) < 0.9 else Vector3.RIGHT).normalized()
		var w := ax.cross(u)
		var lb := v.size()
		for e in 4:
			var t := TAU * e / 4.0
			var off := (u * cos(t) + w * sin(t))
			v.append(a + off * 0.035)
			v.append(b + off * 0.02)
			nrm.append(off)
			nrm.append(off)
			col.append(limb)
			col.append(limb)
		for e in 4:
			var e2 := (e + 1) % 4
			idx.append_array([lb + e * 2, lb + e2 * 2, lb + e * 2 + 1, lb + e2 * 2, lb + e2 * 2 + 1, lb + e * 2 + 1])
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = v
	arr[Mesh.ARRAY_NORMAL] = nrm
	arr[Mesh.ARRAY_COLOR] = col
	arr[Mesh.ARRAY_INDEX] = idx
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return mesh


static func _canopy_mesh() -> ArrayMesh:
	var sphere := SphereMesh.new()
	sphere.radius = 1.0
	sphere.height = 2.0
	sphere.radial_segments = 7
	sphere.rings = 4
	var src := sphere.get_mesh_arrays()
	var v := PackedVector3Array()
	var nrm := PackedVector3Array()
	var idx := PackedInt32Array()
	for lobe: Array in [[Vector3(0.0, 0.1, 0.0), 0.82], [Vector3(0.42, -0.12, 0.2), 0.62], [Vector3(-0.38, -0.05, -0.28), 0.58]]:
		var at: Vector3 = lobe[0]
		var r: float = lobe[1]
		var base := v.size()
		for k in (src[Mesh.ARRAY_VERTEX] as PackedVector3Array).size():
			var p: Vector3 = src[Mesh.ARRAY_VERTEX][k]
			var bump := 1.0 + 0.18 * sin(p.x * 5.1 + p.y * 3.7 + at.x * 9.0) * cos(p.z * 4.3 - p.y * 2.9)
			v.append(at + Vector3(p.x, maxf(p.y, -0.5), p.z) * r * bump)
			nrm.append(src[Mesh.ARRAY_NORMAL][k])
		for k in (src[Mesh.ARRAY_INDEX] as PackedInt32Array):
			idx.append(base + k)
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = v
	arr[Mesh.ARRAY_NORMAL] = nrm
	arr[Mesh.ARRAY_INDEX] = idx
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return mesh


## A model mesh of more than SLICE_OVER triangles (Marvel's seats, a million each; Moorabbin's
## Huggins Stand; People First's two halves) is cut into SLICES pieces by bearing round its own
## middle, the same triangles and materials, so the camera draws only the pieces in its view
## instead of the whole bowl every frame. The picture is unchanged.
static func slice_big_meshes(root: Node, at := [SLICE_OVER, SLICES]) -> void:
	for mi: MeshInstance3D in root.find_children("*", "MeshInstance3D", true, false):
		if mi.mesh == null or mi.skin != null:
			continue
		var tris := 0
		for si in range(mi.mesh.get_surface_count()):
			tris += mi.mesh.surface_get_array_index_len(si) / 3
		if tris <= int(at[0]):
			continue
		var pieces := _slices(mi.mesh, mi, int(at[1]))
		var parent := mi.get_parent()
		for k in range(pieces.size()):
			var piece := MeshInstance3D.new()
			piece.name = "%s_slice%d" % [mi.name, k]
			piece.mesh = pieces[k]
			piece.transform = mi.transform
			piece.material_override = mi.material_override
			piece.cast_shadow = mi.cast_shadow
			parent.add_child(piece)
		parent.remove_child(mi)
		mi.queue_free()


## The mesh's triangles sorted into SLICES meshes by the bearing of each triangle's first corner
## from the middle of the mesh's box; each piece keeps only the corners it uses. With `src_mi`, each
## surface keeps that instance's override (MATERIAL_FIX), not only the mesh's own material.
static func _slices(mesh: Mesh, src_mi: MeshInstance3D = null, count := SLICES) -> Array:
	var mid := mesh.get_aabb().get_center()
	var meshes := []
	for k in range(count):
		meshes.append(ArrayMesh.new())
	for si in range(mesh.get_surface_count()):
		var arr := mesh.surface_get_arrays(si)
		var verts: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
		if idx.is_empty():
			idx.resize(verts.size())
			for i in range(verts.size()):
				idx[i] = i
		var per := []
		for k in range(count):
			per.append(PackedInt32Array())
		for t in range(0, idx.size() - 2, 3):
			var v := verts[idx[t]]
			var k := int(fposmod(atan2(v.z - mid.z, v.x - mid.x), TAU) / TAU * count) % count
			per[k].append(idx[t])
			per[k].append(idx[t + 1])
			per[k].append(idx[t + 2])
		var remap := PackedInt32Array()
		remap.resize(verts.size())
		var mat := src_mi.get_active_material(si) if src_mi != null else mesh.surface_get_material(si)
		for k in range(count):
			var tri: PackedInt32Array = per[k]
			if tri.is_empty():
				continue
			remap.fill(-1)
			var used := PackedInt32Array()
			for j in range(tri.size()):
				var o := tri[j]
				if remap[o] < 0:
					remap[o] = used.size()
					used.append(o)
				tri[j] = remap[o]
			var out := []
			out.resize(Mesh.ARRAY_MAX)
			for a in [Mesh.ARRAY_VERTEX, Mesh.ARRAY_NORMAL, Mesh.ARRAY_TEX_UV, Mesh.ARRAY_TEX_UV2, Mesh.ARRAY_COLOR]:
				if arr[a] != null and arr[a].size() == verts.size():
					out[a] = _pick(arr[a], used)
			if arr[Mesh.ARRAY_TANGENT] != null and arr[Mesh.ARRAY_TANGENT].size() == verts.size() * 4:
				var tan: PackedFloat32Array = arr[Mesh.ARRAY_TANGENT]
				var nt := PackedFloat32Array()
				nt.resize(used.size() * 4)
				for j in range(used.size()):
					for c in range(4):
						nt[j * 4 + c] = tan[used[j] * 4 + c]
				out[Mesh.ARRAY_TANGENT] = nt
			out[Mesh.ARRAY_INDEX] = tri
			var am: ArrayMesh = meshes[k]
			am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, out)
			am.surface_set_material(am.get_surface_count() - 1, mat)
	return meshes.filter(func(m: ArrayMesh) -> bool: return m.get_surface_count() > 0)


## The entries of a per-corner array at the corners `used`, in that order.
static func _pick(src, used: PackedInt32Array):
	var dst = src.duplicate()
	dst.resize(used.size())
	for j in range(used.size()):
		dst[j] = src[used[j]]
	return dst


## Shows ground `slug`'s roof shut or open (ROOFS) on `root`, a ground instantiate() built.
static func set_roof(root: Node, slug: String, shut: bool) -> void:
	var r: Dictionary = ROOFS.get(slug, {})
	if r.is_empty():
		return
	for n in root.find_children(str(r["shut"]) + "*", "", true, false):
		if n is Node3D:
			n.visible = shut
	for n in root.find_children(str(r["open"]) + "*", "", true, false):
		if n is Node3D:
			n.visible = not shut
	# Under the shut roof no sun reaches the ground: the roof's lights light it evenly, so nothing of
	# the stadium throws a sun shadow on the field or the stands. Open, its shadows come back.
	for n in root.find_children("*", "GeometryInstance3D", true, false):
		var g := n as GeometryInstance3D
		if not g.has_meta("roof_cast"):
			g.set_meta("roof_cast", g.cast_shadow)
		g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if shut else g.get_meta("roof_cast")


## Is ground `slug`'s roof shut on `root`?
static func roof_shut(root: Node, slug: String) -> bool:
	var r: Dictionary = ROOFS.get(slug, {})
	if r.is_empty():
		return false
	for n in root.find_children(str(r["shut"]) + "*", "", true, false):
		if n is Node3D:
			return n.visible
	return false


## How far a camera sees when the ground has its surroundings (backdrop()): the city skyline and
## the hills. Without them the match view stops at 900 m.
const BACKDROP_FAR := 7000.0
## Grounds whose CBD skyline stands further off than that see further (Whitten Oval and Windy Hill: the
## city towers 7 to 8.5 km away; North Hobart and Macquarie Point: kunanyi / Mount Wellington, its
## summit 7 km off and its slopes beyond), the haze ending where it does elsewhere.
const BACKDROP_FAR_AT := {"whitten": 9000.0, "windy_hill": 9500.0, "north_hobart": 14000.0, "macpoint": 14000.0}
## Grounds whose backdrop runs further, [camera far, haze end] in m.
const BACKDROP_RANGE := {
		# Manuka: the Brindabellas stand on Canberra's western skyline 25 km out, Black Mountain's tower 5.4 km.
		"manuka": [32000.0, 70000.0],
		# Bellerive reaches kunanyi / Mount Wellington, 11 km across the Derwent, which a Hobart crowd sees clearly.
		"bellerive": [20000.0, 60000.0],
		# Cazaly's reaches the ranges behind Cairns and the sea, which the crowd sees clearly, blue with the distance.
		"cazalys": [56000.0, 150000.0],
		"norwood": [23000.0, 60000.0],
		# York Park reaches the hills round Launceston out to Mount Barrow.
		"york_park": [26000.0, 70000.0],
		# Traeger Park's runs to the MacDonnell Ranges' ridges 20 km east and west in clear desert air.
		"traeger": [24000.0, 90000.0]}


static func backdrop_far(slug: String) -> float:
	return float(BACKDROP_RANGE[slug][0]) if BACKDROP_RANGE.has(slug) else float(BACKDROP_FAR_AT.get(slug, BACKDROP_FAR))


static func backdrop_haze(slug: String, default_to: float) -> float:
	return float(BACKDROP_RANGE[slug][1]) if BACKDROP_RANGE.has(slug) else default_to


## The ground's surroundings past its own street (row 202 2b, the background scenes): the park,
## the streets, the houses, the trees and the skyline, built in Blender round the stadium model in
## the model's own metres (.claude/review/<ground>_bg) and cut down for a phone by
## tools/grounds/backdrop/reduce.py into <slug>_backdrop.glb (or _backdrop_part1.glb ...). Laid
## with the model (it is the model's child), so it fits wherever the model fits. Looks only: it
## casts no shadow into the stadium and nothing in play reads it. null when the ground has none.
static func backdrop(slug: String, base := "") -> Node3D:
	var dir := base if base != "" else DIR + slug + "/"
	var paths := files(slug + "_backdrop", dir)
	if paths.is_empty():
		return null
	var root := Node3D.new()
	root.name = "Backdrop"
	for path in paths:
		var model := load_glb(path)
		if model == null:
			continue
		for gi in model.find_children("*", "GeometryInstance3D", true, false):
			(gi as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_backdrop_materials(model, dir + slug + "_plain.webp")
		root.add_child(model)
	return root


## A model's own far ground, hidden when its backdrop is drawn (the two would fight for a pixel):
## Adelaide's model carries a 6 km grass plane; the ground kit's first drafts (#1930) a 240 m concourse disc;
## the WACA, Bruce and North Hobart a flat plate round the stands (tools/grounds/backdrop/scene: run1.sh SKIP).
const BACKDROP_HIDES := {"adelaide": ["ao_ground"], "barossa": ["concourse"], "sky": ["concourse"],
	"jiangwan": ["concourse"], "hands": ["concourse"], "blacktown": ["concourse_far"], "summit": ["concourse"],
	"macpoint": ["concourse"], "waca": ["land", "road", "brick"], "bruce": ["g_ground"], "north_hobart": ["ground"],
	"traeger": ["ground_dirt"]}

const BACKDROP_SHADER := preload("res://scripts/ui/match/oval3d_backdrop.gdshader")
const BACKDROP_LEAF_SHADER := preload("res://scripts/ui/match/oval3d_backdrop_leaf.gdshader")
const TERRAIN_SHADER := preload("res://scripts/ui/match/oval3d_terrain.gdshader")


## The scene's materials as Blender drew them: the trees and everything else tinted by their
## vertex colours; the walls and roofs (facade_*, roof_*) through oval3d_backdrop.gdshader, which
## leaves their glass and frames untinted; one-sided cut-out leaf cards through
## oval3d_backdrop_leaf.gdshader. Materials are shared, so each is made once.
static func _backdrop_materials(model: Node, plain := "") -> void:
	var made := {}
	for mi in model.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = (mi as MeshInstance3D).mesh
		if mesh == null:
			continue
		# A land mesh with its light already in its vertex colours (Cazaly's ranges, hill-shaded as
		# Google Earth shows them): drawn as coloured, so the sky's blue fill does not turn the
		# rainforest navy.
		if String(mi.name).begins_with("terrain_shaded"):
			if not made.has("terrain_shaded"):
				var tm := ShaderMaterial.new()
				tm.shader = TERRAIN_SHADER
				if plain != "" and ResourceLoader.exists(plain):
					tm.set_shader_parameter("plain", load(plain))
					tm.set_shader_parameter("has_plain", true)
				made["terrain_shaded"] = tm
			(mi as MeshInstance3D).material_override = made["terrain_shaded"]
			continue
		# Land, suburbs and far trees lie in the open like the turf: marked open_ground, so
		# Oval3DTurf.light_stands leaves them off the stand shader (whose green-less sky light turned
		# York Park's far hilltops purple). Buildings (facade_*, roof_*, nb_*) stay on it.
		var open := true
		for i in mesh.get_surface_count():
			var m0 := mesh.surface_get_material(i)
			var n0 := m0.resource_name if m0 != null else ""
			if n0.begins_with("facade_") or n0.begins_with("roof_") or n0.begins_with("nb_"):
				open = false
		if open:
			mi.set_meta("open_ground", true)
		for i in mesh.get_surface_count():
			var mat := mesh.surface_get_material(i) as BaseMaterial3D
			if mat == null:
				continue
			var key := mat.resource_name
			if mat.transparency == BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR and mat.cull_mode == BaseMaterial3D.CULL_BACK \
					and not key.begins_with("tree_"):
				# one-sided leaf cards (Traeger's gums): through oval3d_backdrop_leaf.gdshader, as the
				# standard material's alpha scissor drew them black
				if not made.has(key):
					var lm := ShaderMaterial.new()
					lm.shader = BACKDROP_LEAF_SHADER
					lm.set_shader_parameter("tex", mat.albedo_texture)
					made[key] = lm
				(mi as MeshInstance3D).set_surface_override_material(i, made[key])
			elif key.begins_with("facade_") or key.begins_with("roof_"):
				if not made.has(key):
					var sm := ShaderMaterial.new()
					sm.shader = BACKDROP_SHADER
					sm.set_shader_parameter("tex", mat.albedo_texture)
					made[key] = sm
				(mi as MeshInstance3D).set_surface_override_material(i, made[key])
			else:
				# Tinted only where the mesh carries colours: a modelled part (York Park's neighbours)
				# has none, and the tint would read whatever the missing array left behind.
				mat.vertex_color_use_as_albedo = (mesh.surface_get_format(i) & Mesh.ARRAY_FORMAT_COLOR) != 0
				if key.begins_with("headstone"):   # each stone is one face, seen from both sides
					mat.cull_mode = BaseMaterial3D.CULL_DISABLED
				mat.disable_receive_shadows = true   # past the shadow map's reach it reads blue-grey
				if mat.roughness >= 0.7:
					# matte ground (grass, paving, roads, roofs of far blocks): seen at a low angle its sky
					# reflection painted whole suburbs water-blue, so it reflects next to nothing
					mat.metallic_specular = 0.0
					mat.roughness = 1.0
				if key.begins_with("tree_") and mat.transparency == BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR:
					# leaf cards (Cazaly's palms and figs): their vertex colours were written for Blender's
					# light and draw near-black here, so the pale leaf texture takes a plain foliage green
					mat.vertex_color_use_as_albedo = false
					mat.albedo_color = Color(0.5, 0.6, 0.4)


static func has_backdrop(slug: String, base := "") -> bool:
	return not files(slug + "_backdrop", base if base != "" else DIR + slug + "/").is_empty()


## Every seat in the model's own metres (seats_*.bin), for the crowd to sit on (Oval3DCrowd).
static func seat_transforms(slug: String, base := "") -> Array:
	var dir := base if base != "" else DIR + slug + "/"
	var seats := []
	if not DirAccess.dir_exists_absolute(dir):
		return seats
	for f in DirAccess.get_files_at(dir):
		if not (f.begins_with("seats_") and f.ends_with(".bin")):
			continue
		var buf := FileAccess.get_file_as_bytes(dir + f).to_float32_array()
		for i in range(0, buf.size() - 11, 12):
			seats.append(Transform3D(Basis(Vector3(buf[i], buf[i + 4], buf[i + 8]),
					Vector3(buf[i + 1], buf[i + 5], buf[i + 9]), Vector3(buf[i + 2], buf[i + 6], buf[i + 10])),
					Vector3(buf[i + 3], buf[i + 7], buf[i + 11])))
	return seats


## The seat's points (seat_tmpl.bin, else the first seat_tmpl_<colour>.bin): where a supporter sits.
static func seat_points(slug: String, base := "") -> PackedVector3Array:
	var dir := base if base != "" else DIR + slug + "/"
	var path := dir + "seat_tmpl.bin"
	if not FileAccess.file_exists(path):
		path = ""
		for f in DirAccess.get_files_at(dir):
			if f.begins_with("seat_tmpl_") and f.ends_with(".bin"):
				path = dir + f
				break
	var pts := PackedVector3Array()
	if path == "":
		return pts
	var tmpl := FileAccess.get_file_as_bytes(path).to_float32_array()
	for i in range(0, tmpl.size() - 2, 3):
		pts.append(Vector3(tmpl[i], tmpl[i + 1], tmpl[i + 2]))
	return pts


static func _seat_mesh(path: String) -> Mesh:
	var tmpl := FileAccess.get_file_as_bytes(path).to_float32_array()
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(0, tmpl.size() - 2, 3):
		st.add_vertex(Vector3(tmpl[i], tmpl[i + 1], tmpl[i + 2]))
	st.generate_normals()
	return st.commit()


## True when a seat mesh is an open sheet rather than a closed solid: a closed one's faces,
## weighted by area, point every way and cancel out; a sheet's mostly point one way.
static func _is_sheet(seat: Mesh) -> bool:
	var f := seat.get_faces()
	var sum := Vector3.ZERO
	var area := 0.0
	for i in range(0, f.size() - 2, 3):
		var n := (f[i + 1] - f[i]).cross(f[i + 2] - f[i])
		sum += n
		area += n.length()
	return area > 0.0 and sum.length() > 0.3 * area


static func _add_seats(root: Node3D, dir: String, mid: Vector2) -> void:
	var shared: Mesh = null
	if FileAccess.file_exists(dir + "seat_tmpl.bin"):
		shared = _seat_mesh(dir + "seat_tmpl.bin")
	for f in DirAccess.get_files_at(dir):
		if not (f.begins_with("seats_") and f.ends_with(".bin")):
			continue
		var colour := f.get_basename().trim_prefix("seats_")
		var seat := shared
		if FileAccess.file_exists(dir + "seat_tmpl_%s.bin" % colour):
			seat = _seat_mesh(dir + "seat_tmpl_%s.bin" % colour)
		if seat == null:
			continue
		_instances(root, seat, dir + f, colour, mid)
		if SEAT_FAR.has(dir.get_base_dir().get_file()):
			_instances(root, _seat_far_mesh(), dir + f, colour, mid, _seat_far_material(colour))
	if FileAccess.file_exists(dir + "leg_tmpl.bin"):
		var leg := _seat_mesh(dir + "leg_tmpl.bin")
		for f in DirAccess.get_files_at(dir):
			if f.begins_with("legs_") and f.ends_with(".bin"):
				_instances(root, leg, dir + f, f.get_basename().trim_prefix("legs_"), mid)


## Batches of `mesh` at every transform in the .bin at `path`, flat in SEAT_COLOURS[colour], added
## to `root`: one batch a slice of the bowl (SEAT_SECTORS round it, by bearing from `mid`), so the
## camera draws only the slices in its view, not every seat in the ground.
static func _instances(root: Node3D, mesh: Mesh, path: String, colour: String, mid: Vector2,
		far: Material = null) -> void:
	var buf := FileAccess.get_file_as_bytes(path).to_float32_array()
	var ground := path.get_base_dir().get_file()
	var mat: Material = far
	if mat == null:
		var sm := StandardMaterial3D.new()
		sm.albedo_color = SEAT_COLOURS.get(colour, Color.GRAY)
		# A seat drawn as one open sheet (the ground kit's moulded shell, wound the other way to
		# Godot's front face) is seen from both sides; a closed seat keeps back faces culled.
		if _is_sheet(mesh):
			sm.cull_mode = BaseMaterial3D.CULL_DISABLED
		mat = sm
		if SEAT_FAR.has(ground):
			# the shells give way to the far rows (_seat_far_material) seat by seat (seat_near.gdshader)
			var nm := ShaderMaterial.new()
			nm.shader = SEAT_NEAR_SHADER
			nm.set_shader_parameter("albedo", sm.albedo_color)
			nm.set_shader_parameter("fade_from", SEAT_FAR_FROM)
			nm.set_shader_parameter("fade_to", SEAT_FAR_TO)
			mat = nm
	var per := []
	for i in range(SEAT_SECTORS):
		per.append(PackedFloat32Array())
	for i in range(0, buf.size() - 11, 12):
		var th := fposmod(atan2(buf[i + 11] - mid.y, buf[i + 3] - mid.x), TAU)
		var k := int(th / TAU * SEAT_SECTORS) % SEAT_SECTORS
		per[k].append_array(buf.slice(i, i + 12))
	for k in range(SEAT_SECTORS):
		if per[k].is_empty():
			continue
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = mesh
		mm.instance_count = per[k].size() / 12
		mm.buffer = per[k]
		var mi := MultiMeshInstance3D.new()
		mi.name = "%s_%d" % [path.get_file().get_basename(), k]
		mi.multimesh = mm
		mi.material_override = mat
		if far != null:
			mi.name += "_far"
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			root.add_child(mi)
			continue
		mi.set_meta("seats", true)
		# Grounds whose rows read striped when every seat throws its own shadow on the tread behind it
		# (a dark band a row, aliased into moire from the broadcast camera): their seats cast none.
		if SEATS_NO_SHADOW.has(ground):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		root.add_child(mi)


## The far rows: past SEAT_FAR_FROM m a seat shell is under a few pixels and its 6 cm gaps and its rows
## alias into speckle and moire (PC seat checks, Bellerive 2026-11-23). There each seat is one quad the
## full 0.52 m width (on a 0.5 m pitch, so a row's quads meet edge to edge), from the top of its back
## to the front of its tread (a 0.9 m row rising 0.4 m), painted as the shell looks from the field:
## back and pan, the gaps either side, a strip of tread and the riser's shadow line under it. The
## texture's mipmaps average the gaps and the row lines away as the seat shrinks, as a photo of a
## stand does; seat_far.gdshader lights it as the shell's back and pan would be lit, so the far rows
## take the near shells' tone. Same transforms as the shells.
static func _seat_far_mesh() -> Mesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var w := 0.26
	var q := [Vector3(-w, 0.87, -0.05), Vector3(w, 0.87, -0.05), Vector3(w, 0.0, 0.6), Vector3(-w, 0.0, 0.6)]
	var uv := [Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)]
	st.set_normal(Vector3(0.0, 0.325, 0.49).normalized())   # the back's and the pan's normals, mixed as lit
	for i: int in [0, 1, 2, 0, 2, 3]:
		st.set_uv(uv[i])
		st.add_vertex(q[i])
	return st.commit()


static func _seat_far_material(colour: String) -> ShaderMaterial:
	var c: Color = SEAT_COLOURS.get(colour, Color.GRAY)
	var tread := Color8(198, 200, 198)       # the stepped rows' concrete (tools/grounds/bellerive/model/paint.py)
	var gap := tread.darkened(0.35)          # between two seats: the concrete behind, in their shade
	var img := Image.create(64, 64, false, Image.FORMAT_RGB8)
	for y in range(64):
		for x in range(64):
			var u := (x + 0.5) / 64.0
			var v := (y + 0.5) / 64.0
			var p := c
			if v > 0.9:
				p = tread.darkened(0.7)      # the riser's shadow line: the row's edge, bold enough to
			elif v > 0.8:                    # stay a line in the far mips (PC check r5: a flat sheet)
				p = tread.darkened(0.45)
			elif u < 0.06 or u > 0.94:
				p = gap
			img.set_pixel(x, y, p)
	img.generate_mipmaps()
	var mat := ShaderMaterial.new()
	mat.shader = SEAT_FAR_SHADER
	mat.set_shader_parameter("tex", ImageTexture.create_from_image(img))
	mat.set_shader_parameter("fade_from", SEAT_FAR_FROM)
	mat.set_shader_parameter("fade_to", SEAT_FAR_TO)
	return mat


## MATERIAL_FIX: each named material on `model` gets its own copy with the listed values.
## One PARTS entry: its mesh added to the model, the nodes it replaces taken out.
static func _add_part(model: Node, dir: String, part: Dictionary) -> void:
	if not FileAccess.file_exists(dir + str(part["mesh"])):
		return
	for n: String in part.get("hide", []):
		var old := model.find_child(n, true, false)
		if old != null:
			old.get_parent().remove_child(old)
			old.queue_free()
	var buf := FileAccess.get_file_as_bytes(dir + str(part["mesh"])).to_float32_array()
	var v := PackedVector3Array()
	var nrm := PackedVector3Array()
	var col := PackedColorArray()
	# Godot fronts a triangle wound clockwise; the tools write them either way, with the normal.
	for t in range(0, buf.size() - 26, 27):
		var p := [Vector3(buf[t], buf[t + 1], buf[t + 2]), Vector3(buf[t + 9], buf[t + 10], buf[t + 11]),
				Vector3(buf[t + 18], buf[t + 19], buf[t + 20])]
		var n := Vector3(buf[t + 3], buf[t + 4], buf[t + 5])
		var order := [0, 1, 2] if (p[1] - p[0]).cross(p[2] - p[0]).dot(n) < 0.0 else [0, 2, 1]
		for k: int in order:
			var i: int = t + k * 9
			v.append(p[k])
			nrm.append(Vector3(buf[i + 3], buf[i + 4], buf[i + 5]))
			col.append(Color(buf[i + 6], buf[i + 7], buf[i + 8]))
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = v
	arr[Mesh.ARRAY_NORMAL] = nrm
	arr[Mesh.ARRAY_COLOR] = col
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var mat := StandardMaterial3D.new()
	mat.resource_name = "steel_truss"
	mat.vertex_color_use_as_albedo = true
	mat.roughness = 0.6
	mat.metallic = 0.2
	mesh.surface_set_material(0, mat)
	var mi := MeshInstance3D.new()
	mi.name = str(part.get("name", "Part"))
	mi.mesh = mesh
	model.add_child(mi)


## Glass and other see-through materials drawn with plain alpha. The glTF importer gives a blended
## material a depth pre-pass, and the mobile renderer draws such a surface black where it stands in
## shade (Manuka's glass balustrades under the stand roofs, 2026-11-22).
static func _plain_alpha(model: Node) -> void:
	for mi in model.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = (mi as MeshInstance3D).mesh
		for i in (mesh.get_surface_count() if mesh != null else 0):
			var mat := mesh.surface_get_material(i) as BaseMaterial3D
			if mat != null and mat.transparency == BaseMaterial3D.TRANSPARENCY_ALPHA_DEPTH_PRE_PASS:
				mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA


## Paving and practice wickets a model lays on the land outside the bowl, by mesh name: lit like the
## land round them (the surrounds), not like a stand. Under a stand's light and its shade they read a
## saturated blue beside sunlit grass (Bellerive's practice nets, 2026-11-22).
const OPEN_GROUND := {"bellerive": ["nets_ground", "forecourt"]}


static func _open_ground(model: Node, names: Array) -> void:
	for mi: MeshInstance3D in model.find_children("*", "MeshInstance3D", true, false):
		if mi.mesh == null or not names.any(func(n: String) -> bool: return str(mi.name).begins_with(n)):
			continue
		mi.set_meta("open_ground", true)
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		for i in mi.mesh.get_surface_count():
			var m := mi.get_active_material(i) as BaseMaterial3D
			if m != null:
				var own := m.duplicate() as BaseMaterial3D
				own.disable_receive_shadows = true
				own.roughness = 1.0
				mi.set_surface_override_material(i, own)


static func _fix_materials(model: Node, fixes: Dictionary) -> void:
	var done := {}
	for mi: MeshInstance3D in model.find_children("*", "MeshInstance3D", true, false):
		if mi.mesh == null:
			continue
		for i in mi.mesh.get_surface_count():
			var m := mi.get_active_material(i) as StandardMaterial3D
			if m == null or not fixes.has(m.resource_name):
				continue
			if not done.has(m):
				var own := m.duplicate() as StandardMaterial3D
				var f: Dictionary = fixes[m.resource_name]
				for k: String in f:
					own.set(k, f[k])
				done[m] = own
			mi.set_surface_override_material(i, done[m])


## Every material on `model` paints with its vertex colours (linear, as glTF stores them).
static func _paint_vertex_colours(model: Node) -> void:
	for mi in model.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = (mi as MeshInstance3D).mesh
		if mesh == null:
			continue
		for i in mesh.get_surface_count():
			var mat := mesh.surface_get_material(i) as BaseMaterial3D
			if mat != null:
				mat.vertex_color_use_as_albedo = true
