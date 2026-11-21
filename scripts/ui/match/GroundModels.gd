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
## The match's boundary fence: half its length and width (Oval3D: the playing surface plus FENCE).
const MATCH_FENCE := Vector2(MatchMotion.HALF_LEN + 6.0, MatchMotion.HALF_WID + 6.0)
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
	"optus": [-30.38, 8.77, 0.0, -14.3, 88.5, 69.68],
	"scg": [0.34, 6.68, 0.05, 85.8, 84.43, 72.25],
	"gmhba": [-8.89, 11.85, 0.02, -69.8, 94.3, 66.01],
	"people_first": [-0.72, 0.04, 0.02, -72.6, 89.11, 72.26],
	"engie": [20.64, -43.32, 0.0, -41.1, 92.14, 76.44],
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
	"cazalys": [-0.1, 4.55, -0.01, 61.9, 87.98, 75.36],
	"north_hobart": [-6.71, 0.91, 0.0, -43.8, 81.59, 60.47],
	"bruce": [21.36, -39.57, 0.4, -56.7, 104.51, 64.28],
	"riverway": [-0.41, 1.12, 0.0, -89.9, 86.05, 72.72],
	# The seven first drafts (#1930) are built round their fence: centre at the origin (Summit
	# 2 m off), floor 0. Jiangwan is a running-track stadium; its boundary was placed by judgement.
	"barossa": [0.0, 0.0, 0.0, 72.7, 85.63, 65.98],
	"sky": [0.0, 0.0, 0.0, -77.7, 81.66, 63.74],
	"jiangwan": [0.0, 0.0, 0.0, 63.0, 84.0, 63.0],
	"hands": [0.0, 0.0, 0.0, -61.7, 92.51, 78.09],
	"blacktown": [0.0, 0.0, 0.0, 79.9, 86.29, 72.12],
	"summit": [-1.9, 0.75, 0.0, -83.5, 86.34, 76.17],
	"macpoint": [0.0, 0.0, 0.0, 35.0, 85.0, 72.0],
	# Adelaide Oval's model (#1856) exported for the game by tools/grounds/adelaide/export.py, and the
	# Gabba's model (tools/grounds/gabba), measured the same way.
	"adelaide": [-0.4, 1.37, 0.0, -102.0, 91.36, 65.7],
	"gabba": [2.47, 3.47, 0.0, 175.0, 86.88, 73.71],
}

## Models that carry their colours on the vertices (glTF COLOR_0) under a tiling detail texture.
## Godot's glTF reader keeps the colours but does not paint with them, so the loader turns that on.
const VERTEX_COLOURED := ["adelaide"]

## Each seat colour as the model paints it (the mean of its seat texture; sRGB).
const SEAT_COLOURS := {
	# Accor: aqua lower bowl (seat_teal there keeps the value already here).
	"seat_aqua": Color(0.527, 0.719, 0.757),
	"seat_grey": Color(0.618, 0.618, 0.586), "seat_moss": Color(0.437, 0.594, 0.555),
	"seat_navy": Color(0.068, 0.311, 0.484), "seat_slate": Color(0.272, 0.39, 0.488),
	"seat_steel": Color(0.437, 0.484, 0.524),
	"seat_green": Color(0.314, 0.549, 0.455), "seat_teal": Color(0.384, 0.620, 0.541),
	"seat_blue": Color(0.2, 0.318, 0.467), "seat_paleblue": Color(0.482, 0.612, 0.714),
	"seat_mint": Color(0.502, 0.706, 0.655), "seat_dkgreen": Color(0.039, 0.243, 0.125),
	"seat_greyblue": Color(0.361, 0.471, 0.525),
	"s_blue": Color(0.211, 0.28, 0.448), "s_orange": Color(0.785, 0.426, 0.158),
	"s_grey": Color(0.64, 0.648, 0.663), "s_maroon": Color(0.443, 0.129, 0.16),
	"s_gold": Color(0.863, 0.649, 0.129), "s_teal": Color(0.135, 0.479, 0.456),
	# Optus: each tier's colour pushed grey-blue or tan, from the reference photos (optus_model/build.py).
	"seat_lo_blue": Color(0.802, 0.807, 0.841), "seat_lo_tan": Color(0.892, 0.824, 0.751),
	"seat_mid_blue": Color(0.920, 0.858, 0.794), "seat_mid_tan": Color(1.0, 0.875, 0.704),
	"seat_up_blue": Color(0.653, 0.705, 0.782), "seat_up_tan": Color(0.743, 0.722, 0.693),
	# York Park's teal-green plastic (york_park/model/paint.py), the SCG's two seat colours
	# (their glb material colours, linear -> sRGB).
	"seat_plastic": Color(0.255, 0.365, 0.33),
	"seat_scg_teal": Color(0.125, 0.443, 0.427), "seat_scg_maroon": Color(0.443, 0.125, 0.163),
	# The seven first drafts (#1930; Jiangwan and Summit have no seats).
	"seat_barossa": Color(0.197, 0.212, 0.235), "seat_hands": Color(0.151, 0.319, 0.502),
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


## Every ground that has a model, by its name.
static func grounds() -> Array:
	return GROUNDS.keys()


## How the model is laid on the match ground: its fence centre to the middle, its arena floor just
## under the turf, its long axis along the ground (x), and stretched across the ground so its fence
## meets the match's fence (how far each way: stretch()).
static func fit_transform(slug: String) -> Transform3D:
	if not FIT.has(slug):
		return Transform3D.IDENTITY
	var f: Array = FIT[slug]
	var s := stretch(slug)
	var basis := Basis.from_scale(Vector3(s.x, 1.0, s.y)) * Basis(Vector3.UP, deg_to_rad(float(f[3])))
	var centre := Vector3(float(f[0]), float(f[2]), float(f[1]))
	return Transform3D(basis, -(basis * centre) - Vector3(0.0, UNDER_TURF, 0.0))


## How much the model is stretched along (x) and across (y) the ground to meet the match's fence.
static func stretch(slug: String) -> Vector2:
	var f: Array = FIT.get(slug, [0, 0, 0, 0, MATCH_FENCE.x, MATCH_FENCE.y])
	return Vector2(MATCH_FENCE.x / float(f[4]), MATCH_FENCE.y / float(f[5]))


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
			root.add_child(model)
	_add_seats(root, dir)
	return root


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


static func _add_seats(root: Node3D, dir: String) -> void:
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
		root.add_child(_instances(seat, dir + f, colour))
	if FileAccess.file_exists(dir + "leg_tmpl.bin"):
		var leg := _seat_mesh(dir + "leg_tmpl.bin")
		for f in DirAccess.get_files_at(dir):
			if f.begins_with("legs_") and f.ends_with(".bin"):
				root.add_child(_instances(leg, dir + f, f.get_basename().trim_prefix("legs_")))


## One MultiMesh of `mesh` at every transform in the .bin at `path`, flat in SEAT_COLOURS[colour].
static func _instances(mesh: Mesh, path: String, colour: String) -> MultiMeshInstance3D:
	var buf := FileAccess.get_file_as_bytes(path).to_float32_array()
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = mesh
	mm.instance_count = buf.size() / 12
	mm.buffer = buf
	var mi := MultiMeshInstance3D.new()
	mi.name = path.get_file().get_basename()
	mi.multimesh = mm
	var mat := StandardMaterial3D.new()
	mat.albedo_color = SEAT_COLOURS.get(colour, Color.GRAY)
	# A seat drawn as one open sheet (the ground kit's moulded shell, wound the other way to
	# Godot's front face) is seen from both sides; a closed seat keeps back faces culled.
	if _is_sheet(mesh):
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mi.material_override = mat
	return mi


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
