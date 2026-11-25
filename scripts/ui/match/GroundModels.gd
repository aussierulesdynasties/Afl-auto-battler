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
	"Mars Stadium": "mars",
}

## Each model's boundary fence, measured off the model (tools/grounds/fit_fence.py: an ellipse
## fitted to where a level line 0.5 m above the arena floor first meets the model, looking out
## from the middle): [centre x, centre z, arena floor y, long axis in degrees from +x towards +z,
## half length, half width], in the model's own metres. The MCG's floor is the 4.2 m its loader
## was built on (#1843); its drain line sits a metre lower. Bellerive and Windy Hill were refitted to
## the fence the game draws (tools/visual/preinspect_grounds.gd, 2026-11-21): the first fits left a
## stand up to 20 m inside Bellerive's boundary and Windy Hill's turned 6 degrees off.
const FIT := {
	"mcg": [0.53, 0.39, -4.2, -3.3, 87.19, 73.39],
	"marvel": [-0.03, -0.02, 5.4, -89.8, 90.45, 75.93],
	"optus": [-27.32, 5.16, 0.0, -11.07, 88.91, 69.92],   # bowl front ring from Google Earth (tools/grounds/optus/survey)
	"scg": [0.34, 6.68, 0.05, 85.8, 84.43, 72.25],
	"gmhba": [-8.89, 11.85, 0.02, -69.8, 94.3, 66.01],
	"people_first": [-0.72, 0.04, 0.02, -72.6, 89.11, 72.26],
	# ENGIE: an ellipse through the field edge traced from Google Earth (tools/grounds/engie/fit) gives the
	# centre and axis; its halves are a 162 x 126 m field plus FENCE, a metre inside the real 164 x 128, so
	# the game's fence runs 0.6 m (sides) to 3.2 m (ends) outside the grass edge and clears the front rows (2026-11-22).
	"engie": [-4.26, -3.6, 0.0, -44.0, 87.0, 69.0],
	"bellerive": [0.31, -0.64, -0.02, 68.7, 86.9, 66.77],
	"manuka": [5.93, 8.15, 0.03, -82.9, 85.94, 73.1],
	"norwood": [1.96, -3.15, 0.0, 88.3, 88.73, 63.59],
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
	# Cazaly's: Westcourt and Parramatta Park, Mulgrave Road, Moody Creek (tools/grounds/cazalys/surr/surrounds.py),
	# laid on the model's origin (the OSM pitch's centroid); the ranges and the sea are its backdrop (surr/backdrop.py).
	"cazalys": {"y": -0.04, "inner": 95.0, "colour": Color(0.41, 0.47, 0.28),
			"map": "surrounds.webp", "span": 2048.0, "trees": "trees.bin", "buildings": "buildings.bin",
			# Westcourt in Google Earth: white and cream weatherboard Queenslanders, pastel and grey render, some brick.
			"walls": [Color(0.9, 0.9, 0.86), Color(0.86, 0.82, 0.7), Color(0.74, 0.8, 0.78), Color(0.9, 0.9, 0.86),
					Color(0.62, 0.44, 0.35), Color(0.7, 0.7, 0.68), Color(0.82, 0.78, 0.66)],
			# Its iron roofs from above: zincalume, off-white and grey Colorbond, a few green, red and blue.
			"roofs": [Color(0.6, 0.6, 0.58), Color(0.72, 0.72, 0.69), Color(0.42, 0.43, 0.44), Color(0.6, 0.6, 0.58),
					Color(0.32, 0.42, 0.35), Color(0.52, 0.27, 0.22), Color(0.72, 0.72, 0.69), Color(0.36, 0.42, 0.52)]},
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
			"map": "surrounds.webp", "span": 2048.0, "trees": "trees.bin", "buildings": "buildings.bin"},
	# Optus Stadium on the Burswood peninsula: the Swan River, Perth Water, the parks and plaza from
	# OpenStreetMap (tools/grounds/optus/surrounds.py), and its bridges in 3D, Matagarup's arches
	# included (`models`, tools/grounds/optus/bridges.py).
	"optus": {"y": -0.03, "inner": 100.0, "colour": Color(0.45, 0.55, 0.27),
			"map": "surrounds.webp", "span": 2048.0, "trees": "trees.bin", "buildings": "buildings.bin",
			"models": ["bridges.glb"], "tint": Color.WHITE, "building_tint": Color.WHITE},
}

## Parts of a model drawn again from a build tool's own mesh (per vertex x, y, z, normal, colour;
## float32, the model's metres), the model's own nodes named in `hide` left out. The MCG's roof
## trusses are deep pale lattices from Google Earth, not the model's single blue beams
## (tools/grounds/mcg/trusses.py), and its outside walls get a slab edge at every floor
## (tools/grounds/mcg/ledges.py).
const PARTS := {
	"mcg": [{"mesh": "trusses.bin", "hide": ["trusses"], "name": "Trusses"},
			{"mesh": "ledges.bin", "name": "SlabEdges"}],
}

## Per-ground corrections to a model's materials, by material name, checked against Google Earth
## (MCG, 2026-11-21): the MCG's roof sheeting is matte grey from above. Built glossy and part metal,
## it mirrored the blue sky and read white-blue where the real roof reads warm grey; the tints bring
## its sunlit tops to Google Earth's colours (north 189,188,181, east 148,150,145).
const MATERIAL_FIX := {
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
}

## Models that carry their colours on the vertices (glTF COLOR_0) under a tiling detail texture.
## Godot's glTF reader keeps the colours but does not paint with them, so the loader turns that on.
const VERTEX_COLOURED := ["adelaide"]

## Each seat colour as the model paints it (the mean of its seat texture; sRGB).
const SEAT_COLOURS := {
	# Mars Stadium (seat_blue and seat_greyblue there keep the values already here).
	"seat_cream": Color(0.785, 0.747, 0.655), "seat_white": Color(0.815, 0.830, 0.845),
	"seat_navyblue": Color(0.157, 0.235, 0.502), "seat_charcoal": Color(0.141, 0.165, 0.227),
	"seat_slategrey": Color(0.361, 0.392, 0.447), "seat_lightgrey": Color(0.698, 0.714, 0.737),
	# Accor: aqua lower bowl (seat_teal there keeps the value already here).
	"seat_aqua": Color(0.527, 0.719, 0.757),
	# MCG, by tier from Street View on the ground and Google Earth: white and light grey lower and
	# middle tiers, a blue band along the front of the middle tier, teal-blue top tier
	# (grey-green in the Members' north-west).
	"seat_mcg_white": Color(0.96, 0.88, 0.80), "seat_mcg_grey": Color(0.76, 0.70, 0.64),
	"seat_mcg_blue": Color(0.18, 0.32, 0.52), "seat_mcg_teal": Color(0.42, 0.64, 0.66),
	"seat_mcg_sage": Color(0.50, 0.58, 0.56),
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
	"seat_scg_teal": Color(0.125, 0.443, 0.427), "seat_scg_maroon": Color(0.443, 0.125, 0.163),
	# The seven first drafts (#1930; Jiangwan and Summit have no seats).
	"seat_hands": Color(0.151, 0.319, 0.502),
	"seat_sky_gold": Color(0.778, 0.609, 0.197), "seat_sky_grey": Color(0.266, 0.281, 0.304),
	"seat_bt": Color(0.135, 0.197, 0.349), "seat_mp": Color(0.219, 0.25, 0.296),
	# Adelaide Oval's stand colours, as its model paints them (tools/grounds/adelaide/export.py).
	"seat_ao_navy": Color8(35, 55, 77), "seat_ao_charcoal": Color8(70, 70, 75),
	"seat_ao_slate": Color8(95, 105, 118), "seat_ao_sage": Color8(95, 118, 112),
	"seat_ao_red": Color8(150, 45, 50), "seat_ao_orange": Color8(200, 62, 36),
	# The Gabba's seat mix (tools/grounds/gabba/mktex_hand.py, from photo g49) and its steel seat legs.
	"seat_gabba_gold": Color8(226, 168, 30), "seat_gabba_orange": Color8(222, 120, 34),
	"seat_gabba_white": Color8(236, 236, 230), "seat_gabba_blue": Color8(34, 64, 152),
	"gabba_steel": Color(0.45, 0.46, 0.47),
}


## The model folder a match at `ground` plays in, "" when the ground has no model yet.
static func slug_for(ground: String) -> String:
	if GROUNDS.has(ground):
		return str(GROUNDS[ground])
	# GameDB through the tree, so tools that load this before the autoloads still compile.
	var tree := Engine.get_main_loop() as SceneTree
	var db: Node = tree.root.get_node_or_null("GameDB") if tree != null else null
	return str(GROUNDS.get(db.ground_key(ground), "")) if db != null else ""


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
			for part: Dictionary in PARTS.get(slug, []):
				_add_part(model, dir, part)
			root.add_child(model)
	slice_big_meshes(root)
	var fit: Array = FIT.get(slug, [0.0, 0.0])
	_add_seats(root, dir, Vector2(float(fit[0]), float(fit[1])))
	if SURROUNDS.has(slug):
		_add_surrounds(root, SURROUNDS[slug], dir)
	var bd := backdrop(slug, dir)
	if bd != null:
		root.add_child(bd)
		for n: String in BACKDROP_HIDES.get(slug, []):   # the model's own ground, where the scene's takes over
			for mi in root.find_children(n + "*", "MeshInstance3D", true, false):
				(mi as MeshInstance3D).visible = false
	return root


## A flat ring of parkland round the model (SURROUNDS): grass with a broad mottle, unlit by
## nothing it would not be lit by (it takes the sun, the sky and the stands' shade).
static func _add_surrounds(root: Node3D, s: Dictionary, dir := "") -> void:
	if s.has("land"):
		_add_land(root, s, dir)
		return
	var inner: float = s["inner"]
	var outer: float = s.get("outer", 2500.0)
	var y: float = s["y"]
	var n := 96
	var map: Texture2D = null
	if s.has("map") and ResourceLoader.exists(dir + str(s["map"])):
		map = load(dir + str(s["map"]))
	var span: float = s.get("span", 2048.0)
	var v := PackedVector3Array()
	var uv := PackedVector2Array()
	var nrm := PackedVector3Array()
	var idx := PackedInt32Array()
	for i in n + 1:
		var a := TAU * i / n
		var d := Vector3(cos(a), 0.0, sin(a))
		for r: float in RINGS.map(func(f): return f if f > 0.0 else inner) + [outer]:
			var p := d * r + Vector3(0.0, y, 0.0)
			v.append(p)
			# The painted map clamps at its edge (painted plain there); the mottle tiles.
			uv.append(Vector2(p.x, p.z) / span + Vector2(0.5, 0.5) if map != null else Vector2(p.x, p.z) / 60.0)
			nrm.append(Vector3.UP)
	var per := RINGS.size() + 1
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
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	if map != null:
		var mm := StandardMaterial3D.new()
		mm.resource_name = "surrounds"
		mm.albedo_texture = map
		# The sun's shadow map reaches 160 m from the camera; past it, on the Mobile renderer, the
		# land read as if in shade (blue-grey). Its trees' shade is painted into the map instead.
		mm.disable_receive_shadows = true
		mm.texture_repeat = false
		mm.roughness = 1.0
		# `tint` brings the painted map to Google Earth's colours under the match light (Optus).
		mm.albedo_color = s.get("tint", Color.WHITE)
		var g := MeshInstance3D.new()
		g.name = "Surrounds"
		g.mesh = mesh
		g.material_override = mm
		g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		g.set_meta("open_ground", true)
		root.add_child(g)
		if s.has("trees") and FileAccess.file_exists(dir + str(s["trees"])):
			_add_trees(root, FileAccess.get_file_as_bytes(dir + str(s["trees"])).to_float32_array(), y)
		if s.has("buildings") and FileAccess.file_exists(dir + str(s["buildings"])):
			_add_buildings(root, FileAccess.get_file_as_bytes(dir + str(s["buildings"])).to_float32_array(), y,
					s.get("walls", []), s.get("roofs", []), s.get("building_tint", s.get("tint", Color.WHITE)))
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
## Trees are drawn in square blocks this many metres a side, so the camera draws only those in view.
const TREE_BLOCK := 250.0


## Every tree of the map (x, z, height, canopy radius, shade; model metres) as a trunk and a rounded
## canopy, one batch a block of the park. Unlit by their own shadows (the map paints their shade).
static func _add_trees(root: Node3D, buf: PackedFloat32Array, y: float, stride := 5) -> void:
	var canopy := _canopy_mesh()
	var trunk := CylinderMesh.new()
	trunk.top_radius = 0.022
	trunk.bottom_radius = 0.035
	trunk.height = 1.0
	trunk.radial_segments = 5
	trunk.rings = 0
	trunk.cap_top = false
	trunk.cap_bottom = false
	var leaf := StandardMaterial3D.new()
	leaf.resource_name = "tree_leaf"
	leaf.vertex_color_use_as_albedo = true
	leaf.albedo_color = Color(0.27, 0.34, 0.19)
	leaf.roughness = 1.0
	leaf.disable_receive_shadows = true
	var bark := StandardMaterial3D.new()
	bark.resource_name = "tree_bark"
	bark.albedo_color = Color(0.33, 0.29, 0.24)
	bark.roughness = 1.0
	bark.disable_receive_shadows = true
	var blocks := {}
	# Each tree's x, z (and its own ground height when stride is 6) begin its record.
	var zo := 2 if stride == 6 else 1
	var o := 1 if stride == 6 else 0
	for i in range(0, buf.size() - stride + 1, stride):
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
			var at := Vector3(buf[i], buf[i + 1] if stride == 6 else y, buf[i + zo])
			var turn := Basis(Vector3.UP, buf[i + 4 + o] * TAU)
			var crown := h - r * 1.1
			leaves.set_instance_transform(j, Transform3D(turn.scaled(Vector3(r, r * 0.85, r)), at + Vector3(0, crown, 0)))
			# Eucalypt grey-green to elm green, a little lighter or darker tree to tree.
			var shade: float = buf[i + 4 + o]
			leaves.set_instance_color(j, Color(0.92, 0.95, 0.9).lerp(Color(1.1, 1.08, 0.95), shade) * (0.85 + 0.3 * fposmod(shade * 7.3, 1.0)))
			stems.set_instance_transform(j, Transform3D(Basis().scaled(Vector3(h, crown, h)), at + Vector3(0, crown * 0.5, 0)))
		for pair in [[leaves, leaf, "Trees"], [stems, bark, "Trunks"]]:
			var mi := MultiMeshInstance3D.new()
			mi.name = "%s_%d_%d" % [pair[2], key.x, key.y]
			mi.multimesh = pair[0]
			mi.material_override = pair[1]
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			root.add_child(mi)


## The map's buildings round the ground (point count, height, then the footprint's x, z): plain
## walls in a pale render or brick and a flat roof each, as one mesh. Seen past the stands and
## from a fly-through, they set the MCG in its city rather than on a plain.
static func _add_buildings(root: Node3D, buf: PackedFloat32Array, y: float, walls: Array = [],
		roofs: Array = [], tint := Color.WHITE) -> void:
	var v := PackedVector3Array()
	var nrm := PackedVector3Array()
	var col := PackedColorArray()
	const WALLS := [Color(0.86, 0.84, 0.8), Color(0.78, 0.76, 0.72), Color(0.72, 0.6, 0.5), Color(0.9, 0.88, 0.84),
			Color(0.66, 0.66, 0.66)]
	var i := 0
	var b := 0
	while i + 1 < buf.size():
		var n := int(buf[i])
		var h: float = buf[i + 1]
		# A negative height is a house: walls to the eaves at -h, then a hipped roof (GMHBA's Geelong).
		var hipped := h < 0.0
		h = absf(h)
		var foot := PackedVector2Array()
		for k in n:
			foot.append(Vector2(buf[i + 2 + k * 2], buf[i + 3 + k * 2]))
		i += 2 + n * 2
		b += 1
		var wall: Color = walls[b % walls.size()] if not walls.is_empty() else WALLS[b % WALLS.size()]
		var roof := wall.darkened(0.18)
		if hipped:
			var hr: Array = roofs if not roofs.is_empty() else HOUSE_ROOFS
			roof = hr[(b * 7) % hr.size()]
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
		if hipped:
			_hip_roof(foot, y + h, roof, v, nrm, col)
			continue
		var tri := Geometry2D.triangulate_polygon(foot)
		for k in range(0, tri.size() - 2, 3):
			_front(v, nrm, col, Vector3(foot[tri[k]].x, y + h, foot[tri[k]].y),
					Vector3(foot[tri[k + 1]].x, y + h, foot[tri[k + 1]].y),
					Vector3(foot[tri[k + 2]].x, y + h, foot[tri[k + 2]].y), Vector3.UP, roof)
	if v.is_empty():
		return
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = v
	arr[Mesh.ARRAY_NORMAL] = nrm
	arr[Mesh.ARRAY_COLOR] = col
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var mat := StandardMaterial3D.new()
	mat.resource_name = "city"
	mat.vertex_color_use_as_albedo = true
	mat.albedo_color = tint
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.roughness = 0.95
	mat.disable_receive_shadows = true
	var mi := MeshInstance3D.new()
	mi.name = "Buildings"
	mi.mesh = mesh
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.set_meta("open_ground", true)
	root.add_child(mi)


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


## Geelong's house roofs from above in Google Earth: terracotta tile, charcoal and grey Colorbond, pale zinc.
const HOUSE_ROOFS := [Color(0.62, 0.36, 0.28), Color(0.34, 0.34, 0.35), Color(0.55, 0.55, 0.54),
		Color(0.7, 0.42, 0.32), Color(0.45, 0.46, 0.47), Color(0.74, 0.74, 0.72), Color(0.52, 0.3, 0.25)]


## A hipped roof over a house's footprint: each eave rises to a ridge along the footprint's long axis,
## 0.45 of the house's narrow half-width high (about a 24 degree pitch). Faces lit by their slope.
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


## A canopy of about radius 1: two lumpy lobes, one high and one off to the side, so a park of them
## reads as gums and elms rather than balls on sticks.
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
static func slice_big_meshes(root: Node) -> void:
	for mi: MeshInstance3D in root.find_children("*", "MeshInstance3D", true, false):
		if mi.mesh == null or mi.skin != null:
			continue
		var tris := 0
		for si in range(mi.mesh.get_surface_count()):
			tris += mi.mesh.surface_get_array_index_len(si) / 3
		if tris <= SLICE_OVER:
			continue
		var pieces := _slices(mi.mesh, mi)
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
static func _slices(mesh: Mesh, src_mi: MeshInstance3D = null) -> Array:
	var mid := mesh.get_aabb().get_center()
	var meshes := []
	for k in range(SLICES):
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
		for k in range(SLICES):
			per.append(PackedInt32Array())
		for t in range(0, idx.size() - 2, 3):
			var v := verts[idx[t]]
			var k := int(fposmod(atan2(v.z - mid.z, v.x - mid.x), TAU) / TAU * SLICES) % SLICES
			per[k].append(idx[t])
			per[k].append(idx[t + 1])
			per[k].append(idx[t + 2])
		var remap := PackedInt32Array()
		remap.resize(verts.size())
		var mat := src_mi.get_active_material(si) if src_mi != null else mesh.surface_get_material(si)
		for k in range(SLICES):
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


## How far a camera sees when the ground has its surroundings (backdrop()): the city skyline and
## the hills. Without them the match view stops at 900 m.
const BACKDROP_FAR := 7000.0
## Grounds whose backdrop runs further, [camera far, haze end] in m: Cazaly's reaches the ranges
## behind Cairns and the sea, which the crowd sees clearly, blue with the distance.
const BACKDROP_RANGE := {"cazalys": [56000.0, 150000.0]}


static func backdrop_far(slug: String) -> float:
	return float(BACKDROP_RANGE[slug][0]) if BACKDROP_RANGE.has(slug) else BACKDROP_FAR


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
## Adelaide's model carries a 6 km grass plane.
const BACKDROP_HIDES := {"adelaide": ["ao_ground"]}

const BACKDROP_SHADER := preload("res://scripts/ui/match/oval3d_backdrop.gdshader")
const TERRAIN_SHADER := preload("res://scripts/ui/match/oval3d_terrain.gdshader")


## The scene's materials as Blender drew them: the trees and everything else tinted by their
## vertex colours; the walls and roofs (facade_*, roof_*) through oval3d_backdrop.gdshader, which
## leaves their glass and frames untinted. Materials are shared, so each is made once.
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
		for i in mesh.get_surface_count():
			var mat := mesh.surface_get_material(i) as BaseMaterial3D
			if mat == null:
				continue
			var key := mat.resource_name
			if key.begins_with("facade_") or key.begins_with("roof_"):
				if not made.has(key):
					var sm := ShaderMaterial.new()
					sm.shader = BACKDROP_SHADER
					sm.set_shader_parameter("tex", mat.albedo_texture)
					made[key] = sm
				(mi as MeshInstance3D).set_surface_override_material(i, made[key])
			else:
				mat.vertex_color_use_as_albedo = true
				mat.disable_receive_shadows = true   # past the shadow map's reach it reads blue-grey


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
	if FileAccess.file_exists(dir + "leg_tmpl.bin"):
		var leg := _seat_mesh(dir + "leg_tmpl.bin")
		for f in DirAccess.get_files_at(dir):
			if f.begins_with("legs_") and f.ends_with(".bin"):
				_instances(root, leg, dir + f, f.get_basename().trim_prefix("legs_"), mid)


## Batches of `mesh` at every transform in the .bin at `path`, flat in SEAT_COLOURS[colour], added
## to `root`: one batch a slice of the bowl (SEAT_SECTORS round it, by bearing from `mid`), so the
## camera draws only the slices in its view, not every seat in the ground.
static func _instances(root: Node3D, mesh: Mesh, path: String, colour: String, mid: Vector2) -> void:
	var buf := FileAccess.get_file_as_bytes(path).to_float32_array()
	var mat := StandardMaterial3D.new()
	mat.albedo_color = SEAT_COLOURS.get(colour, Color.GRAY)
	# A seat drawn as one open sheet (the ground kit's moulded shell, wound the other way to
	# Godot's front face) is seen from both sides; a closed seat keeps back faces culled.
	if _is_sheet(mesh):
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED
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
		mi.set_meta("seats", true)
		root.add_child(mi)


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
