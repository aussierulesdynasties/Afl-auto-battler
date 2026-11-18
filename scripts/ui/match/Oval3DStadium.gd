extends Node3D
class_name Oval3DStadium
## The 3D view's stadium round the fence (row 202, 3D view plan 2b): the ground's own stands, roof,
## light towers, screens, fence boards, from its entry in data/grounds.json
## (VignetteGround.spec_of). Looks only: nothing here reaches the match sim.
## Each tier is [inner offset, outer offset, inner height, outer height] in metres beyond the fence;
## its crowd sits on it (Oval3DCrowd). Between two tiers: the concourse and the upper tier's front
## wall. Behind the top tier: the back wall, then the roof as the data names it (edge, canopy, closed).
## The main camera (rule 2.93: on the centre line, 15 m up, 25 m back from the boundary) stands on a
## camera platform on each wing, with no seats in front of the lens, as at a real ground.

const SEG := 240
const CAM_UP := 15.0          # m: the main camera's eye above the ground (2.93)
const CAM_BACK := 25.0        # m: ...and back from the boundary
const DECK_W := 9.0           # m: the camera platform along the wing
const DECK_D := 6.0           # m: ...and its depth
const BOARD_H := 1.0          # m: the fence boards
const SIGN_PANELS := 6         # fence panels per sign (about 17 m)

## The fence boards' look, set only by tools/visual/capture_stadium3d.gd to compare the options
## for the director: "plain" (today), "sponsor" or "club". The game draws "plain".
static var fence_look := "plain"

var spec: Dictionary
var tiers: Array = []
var stands: Array = []        # [{t0, t1, tiers, back, top, roof, roof_colour, facade, whole}]
var a := 0.0                  # fence semi-axes (m)
var b := 0.0
var top := 0.0                # the top tier's back row height
var back := 0.0               # the top tier's back offset
var crowd: Oval3DCrowd
var clear: Array = []         # [AABB]: no seat inside (the camera platforms)
var closed := false           # a closed roof: the field is lit from it (rule 2.91)
var lamps: Array = []         # [DirectionalLight3D]: the roof's lights
var home_cols: Array = [Color.NAVY_BLUE, Color.WHITE]
var home_name := ""           # for the "club" boards
var ground_name := ""


func build(p_a: float, p_b: float, p_spec: Dictionary, half_wid: float, home: Array, away: Array) -> void:
	a = p_a
	b = p_b
	spec = p_spec
	home_cols = home
	for t in spec.get("tiers", [[2.0, 26.0, 1.5, 13.0], [30.0, 52.0, 17.0, 34.0]]):
		tiers.append([float(t[0]), float(t[1]), float(t[2]), float(t[3])])
	stands = _stand_list()
	for s: Dictionary in stands:
		back = maxf(back, s["back"])
		top = maxf(top, s["top"])
	_platforms(half_wid)
	crowd = Oval3DCrowd.new()
	crowd.name = "Crowd"
	add_child(crowd)
	crowd.build(a, b, stands, home, away, clear)
	_surrounds()
	for s: Dictionary in stands:
		_bowl(s)
		_roof(s)
	_towers()
	_screens()
	_fence()


## The ground's stands, each {t0, t1, tiers, back, top, roof, roof_colour, facade}: from the data's
## "stands" (each from/to in degrees round the fence: 0 the right-hand end seen from the main
## camera, 90 the camera's wing, 180 the left end, 270 the far wing), or one stand all the way round.
func _stand_list() -> Array:
	var out := []
	var list: Array = spec.get("stands", [{}])
	for d: Dictionary in list:
		var f := deg_to_rad(float(d.get("from", 0.0)))
		var g := deg_to_rad(float(d.get("to", 360.0)))
		if g <= f:
			g += TAU
		var tl := []
		for t in d.get("tiers", tiers):
			tl.append([float(t[0]), float(t[1]), float(t[2]), float(t[3])])
		var last: Array = tl[tl.size() - 1]
		out.append({"t0": f, "t1": g, "tiers": tl, "back": last[1], "top": last[3],
				"roof": str(d.get("roof", spec.get("roof", "edge"))),
				"roof_colour": str(d.get("roof_colour", spec.get("roof_colour", "#0f0f12"))),
				"facade": str(d.get("facade", spec.get("facade", "concrete"))),
				"whole": g - f >= TAU - 0.001})
	return out


## Open ground beyond the fence out to the horizon, under the stands and in their gaps.
func _surrounds() -> void:
	var st := _st()
	var c := Color.html(str(spec.get("surrounds", "#3f4a3a")))
	_band(st, 0.3, -0.03, 900.0, -0.03, c)
	_mesh(st, false)

## Fence-line ellipse point at angle t, d metres out, y up.
func _p(t: float, d: float, y: float) -> Vector3:
	return Vector3(cos(t) * (a + d), y, sin(t) * (b + d))


## A band from (d0, y0) to (d1, y1) round the arc f..g (all the way round by default), lit both sides.
func _band(st: SurfaceTool, d0: float, y0: float, d1: float, y1: float, c: Color, f := 0.0, g := TAU) -> void:
	var n := maxi(1, ceili(SEG * (g - f) / TAU))
	for i in range(n):
		var t0 := f + (g - f) * float(i) / n
		var t1 := f + (g - f) * float(i + 1) / n
		var q := [_p(t0, d0, y0), _p(t0, d1, y1), _p(t1, d1, y1), _p(t1, d0, y0)]
		var nn: Vector3 = (q[1] - q[0]).cross(q[3] - q[0]).normalized()
		# Godot's front faces wind clockwise seen from the normal's side; (0, 1, 2) winds
		# anticlockwise about n, so it is reversed unless n is flipped. A wrong winding shows the
		# back face, whose normal Godot turns over: a roof lit from below, green from the grass.
		var order := [0, 2, 1, 0, 3, 2]
		if nn.y < -0.01 or (absf(nn.y) < 0.01 and nn.dot(-Vector3(cos(t0), 0, sin(t0))) < 0.0):
			# Face up (or in to the field).
			nn = -nn
			order = [0, 1, 2, 0, 2, 3]
		for k in order:
			st.set_normal(nn)
			st.set_color(c)
			st.add_vertex(q[k])


## A quad lit from the side n faces.
func _quad_n(st: SurfaceTool, q: Array, n: Vector3, c: Color) -> void:
	var cr: Vector3 = (q[1] - q[0]).cross(q[3] - q[0])
	var order := [0, 2, 1, 0, 3, 2] if cr.dot(n) > 0.0 else [0, 1, 2, 0, 2, 3]
	for k in order:
		st.set_normal(n)
		st.set_color(c)
		st.add_vertex(q[k])


## A stand's side wall where it ends at angle t: its cross-section, filled down to the ground.
func _end_wall(st: SurfaceTool, s: Dictionary, t: float, out_dir: float, c: Color) -> void:
	var tl: Array = s["tiers"]
	var prof := [Vector2(0.0, 0.0), Vector2(tl[0][0], tl[0][2])]
	for i in range(tl.size()):
		prof.append(Vector2(tl[i][1], tl[i][3]))
		if i + 1 < tl.size():
			prof.append(Vector2(tl[i + 1][0], tl[i][3]))
			prof.append(Vector2(tl[i + 1][0], tl[i + 1][2]))
	prof.append(Vector2(s["back"], s["top"] + 3.0))
	var tan := Vector3(-sin(t) * a, 0.0, cos(t) * b).normalized() * out_dir
	for i in range(prof.size() - 1):
		var p0: Vector2 = prof[i]
		var p1: Vector2 = prof[i + 1]
		if p1.x - p0.x < 0.01:
			continue
		_quad_n(st, [_p(t, p0.x, 0.0), _p(t, p0.x, p0.y), _p(t, p1.x, p1.y), _p(t, p1.x, 0.0)], tan, c)

func _mesh(st: SurfaceTool, shadow := true, mat: Material = null) -> MeshInstance3D:
	var m := mat
	if m == null:
		var sm := StandardMaterial3D.new()
		sm.vertex_color_use_as_albedo = true
		sm.vertex_color_is_srgb = true
		sm.cull_mode = BaseMaterial3D.CULL_DISABLED
		sm.roughness = 0.9
		m = sm
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadow \
			else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)
	return mi


func _st() -> SurfaceTool:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	return st


## A stand's concrete: the apron in front of its first tier, its front wall, each concourse and
## the next tier's front wall, the back wall over the top row, and its side walls where it ends.
func _bowl(s: Dictionary) -> void:
	var st := _st()
	var concrete := Color(0.55, 0.55, 0.54)
	var fascia := Color(0.16, 0.17, 0.2)
	var apron := Color(0.36, 0.38, 0.36)
	var f: float = s["t0"]
	var g: float = s["t1"]
	var tl: Array = s["tiers"]
	var first: Array = tl[0]
	_band(st, 0.0, 0.02, first[0], 0.02, apron, f, g)
	_band(st, first[0], 0.0, first[0], first[2], concrete, f, g)
	for i in range(1, tl.size()):
		var lo: Array = tl[i - 1]
		var hi: Array = tl[i]
		_band(st, lo[1], lo[3], hi[0], lo[3], concrete, f, g)
		_band(st, hi[0], lo[3], hi[0], hi[2], fascia, f, g)
	_band(st, s["back"], 0.0, s["back"], s["top"] + 3.0, concrete, f, g)
	if not s["whole"]:
		_end_wall(st, s, f, -1.0, concrete)
		_end_wall(st, s, g, 1.0, concrete)
	_mesh(st)


## The roof over the top tier, as the ground's data names it. edge: a thin dark lip;
## canopy: a pale roof reaching out over the top tier; closed: a roof over the whole ground.
func _roof(s: Dictionary) -> void:
	var kind: String = s["roof"]
	var c := Color.html(s["roof_colour"])
	var tl: Array = s["tiers"]
	var last: Array = tl[tl.size() - 1]
	var bk: float = s["back"]
	var tp: float = s["top"]
	var f: float = s["t0"]
	var g: float = s["t1"]
	var st := _st()
	match kind:
		"canopy":
			_band(st, bk + 1.0, tp + 8.0, last[0] + 2.0, tp + 5.0, c, f, g)
			_band(st, bk + 1.0, tp + 3.0, bk + 1.0, tp + 8.0, c.darkened(0.3), f, g)
		"closed":
			_band(st, bk + 1.0, tp + 9.0, -2.0, tp + 9.0, c, f, g)
			_band(st, bk + 1.0, tp + 3.0, bk + 1.0, tp + 9.0, c.darkened(0.3), f, g)
		"none":
			return
		_:
			_band(st, bk + 1.0, tp + 5.0, bk - 5.0, tp + 5.0, c, f, g)
			_band(st, bk + 1.0, tp + 3.0, bk + 1.0, tp + 5.0, c, f, g)
	var rim := _mesh(st)
	if kind == "closed":
		closed = true
		# The roof's lights (rule 2.91) shine from under it, so it must not shade them.
		rim.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_roof_lamps()
		# The roof over the field, closed.
		var mi := MeshInstance3D.new()
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		# An elliptical disc on the rim: the roof's colour on top, and underneath the steel
		# frame, light grey and lit by its own floodlights, as it reads from the field.
		var cm := CylinderMesh.new()
		cm.top_radius = 1.0
		cm.bottom_radius = 1.0
		cm.height = 0.6
		cm.radial_segments = 96
		cm.rings = 1
		mi.mesh = cm
		mi.scale = Vector3(a + 2.0, 1.0, b + 2.0)
		var top_m := StandardMaterial3D.new()
		top_m.albedo_color = c
		var under := StandardMaterial3D.new()
		under.albedo_color = Color(0.46, 0.48, 0.52)
		under.emission_enabled = true
		under.emission = Color(0.46, 0.48, 0.52)
		under.emission_energy_multiplier = 0.45
		# A CylinderMesh is one surface: the grey disc below, a thin one of the roof's colour on it.
		mi.material_override = under
		mi.position.y = top + 9.0
		add_child(mi)
		var cap := MeshInstance3D.new()
		cap.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var cc := CylinderMesh.new()
		cc.top_radius = 1.0
		cc.bottom_radius = 1.0
		cc.height = 0.1
		cc.radial_segments = 96
		cc.rings = 1
		cap.mesh = cc
		cap.scale = mi.scale
		cap.material_override = top_m
		cap.position.y = top + 9.35
		add_child(cap)


## Under a closed roof the floodlights sit on the roof all the way round (rule 2.91), day or
## night, as at Marvel: the approved look's rig (tools/visual/capture_look3d.gd "roof"), one
## lamp near overhead with a soft shadow at each man's feet and eight low lamps round the ring.
## Oval3DTurf.apply turns the sun and its fill off when `closed`.
func _roof_lamps() -> void:
	_lamp(0.0, 78.0, 0.9, true, 14.0)
	for az in range(0, 360, 45):
		_lamp(float(az), 38.0, 0.16, false, 1.0)


func _lamp(az: float, el: float, energy: float, shadow: bool, soft: float) -> void:
	var l := DirectionalLight3D.new()
	l.light_color = Color(0.96, 0.98, 1.0)
	l.light_energy = energy
	l.shadow_enabled = shadow
	l.light_angular_distance = soft
	l.directional_shadow_max_distance = 160.0
	add_child(l)
	var r := deg_to_rad(az)
	var e := deg_to_rad(el)
	var from := Vector3(cos(r) * cos(e), sin(e), sin(r) * cos(e))
	l.basis = Basis.looking_at(-from, Vector3.UP)
	lamps.append(l)


## Light towers: the MCG's tall tubular masts, plain masts, or none (lights on the roof).
func _towers() -> void:
	var kind := str(spec.get("towers", "masts"))
	var n := int(spec.get("tower_count", 0))
	if kind == "none" or n <= 0:
		return
	var steel := StandardMaterial3D.new()
	steel.albedo_color = Color(0.78, 0.79, 0.8) if kind == "mcg" else Color(0.5, 0.52, 0.55)
	steel.metallic = 0.4
	steel.roughness = 0.5
	var lamp := StandardMaterial3D.new()
	lamp.albedo_color = Color(0.92, 0.93, 0.9)
	lamp.emission_enabled = true
	lamp.emission = Color(1.0, 0.98, 0.9)
	lamp.emission_energy_multiplier = 0.4
	var h := top + (45.0 if kind == "mcg" else 30.0)
	for i in range(n):
		# Spread round the ground, none on the centre line (the wings' camera ends) or the goal line.
		var t := TAU * (float(i) + 0.5) / float(n)
		var foot := _p(t, back + 4.0, 0.0)
		var mast := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.9 if kind == "mcg" else 0.6
		cm.bottom_radius = 1.6 if kind == "mcg" else 0.9
		cm.height = h
		cm.radial_segments = 16
		mast.mesh = cm
		mast.material_override = steel
		mast.position = foot + Vector3(0, h * 0.5, 0)
		add_child(mast)
		var head := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(12.0 if kind == "mcg" else 8.0, 7.0, 1.2)
		head.mesh = bm
		head.material_override = lamp
		var at := foot + Vector3(0, h, 0)
		head.position = at
		add_child(head)
		head.look_at(Vector3(0, 0, 0), Vector3.UP)
		head.rotate_object_local(Vector3.RIGHT, deg_to_rad(10.0))


## The big screens: one or two, at the ends above the top tier, facing the ground.
func _screens() -> void:
	var n := int(spec.get("screens", 1))
	var frame := StandardMaterial3D.new()
	frame.albedo_color = Color(0.08, 0.08, 0.09)
	var face := StandardMaterial3D.new()
	face.albedo_color = Color(0.04, 0.07, 0.16)
	face.emission_enabled = true
	face.emission = Color(0.1, 0.2, 0.45)
	face.emission_energy_multiplier = 0.6
	var ends := [1.0] if n <= 1 else [1.0, -1.0]
	for e in ends:
		var t: float = 0.0 if e > 0.0 else PI
		var at := _p(t, back - 2.0, top + 9.0)
		for part in [[Vector3(26.0, 12.0, 1.0), frame, 0.0], [Vector3(24.5, 10.5, 0.2), face, -0.55]]:
			var mi := MeshInstance3D.new()
			var bm := BoxMesh.new()
			bm.size = part[0]
			mi.mesh = bm
			mi.material_override = part[1]
			add_child(mi)
			mi.position = at
			mi.look_at(Vector3(0, at.y, 0), Vector3.UP)
			mi.translate_object_local(Vector3(0, 0, part[2]))
		var leg := MeshInstance3D.new()
		var lm := BoxMesh.new()
		lm.size = Vector3(1.5, top + 3.0, 1.5)
		leg.mesh = lm
		leg.material_override = frame
		leg.position = Vector3(at.x, (top + 3.0) * 0.5, at.z)
		add_child(leg)


## The fence: boards all the way round at the boundary's edge, plain panels in two blues and a
## white rail along the top (no sponsor's mark).
func _fence() -> void:
	var st := _st()
	var n := 180
	var signs: Array = _signs()
	for i in range(n):
		var t0 := TAU * float(i) / n
		var t1 := TAU * float(i + 1) / n
		var c := Color(0.07, 0.13, 0.3) if i % 2 == 0 else Color(0.1, 0.2, 0.42)
		if not signs.is_empty():
			var sg: Array = signs[(i / SIGN_PANELS) % signs.size()]
			c = sg[1]
			if i % SIGN_PANELS == SIGN_PANELS / 2:
				_sign_text(t0, str(sg[0]), sg[2])
		var q := [_p(t0, 0.0, 0.0), _p(t0, 0.0, BOARD_H), _p(t1, 0.0, BOARD_H), _p(t1, 0.0, 0.0)]
		var nrm := -Vector3(cos(t0) / a, 0.0, sin(t0) / b).normalized()
		for k in [0, 1, 2, 0, 2, 3]:
			st.set_normal(nrm)
			st.set_color(c)
			st.add_vertex(q[k])
	_band(st, 0.0, BOARD_H, 0.0, BOARD_H + 0.1, Color(0.9, 0.9, 0.88))
	var m := StandardMaterial3D.new()
	m.vertex_color_use_as_albedo = true
	m.vertex_color_is_srgb = true
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.emission_enabled = true
	m.emission = Color(0.05, 0.08, 0.16)
	if not signs.is_empty():
		# LED boards glow with their own colour.
		m.emission_operator = BaseMaterial3D.EMISSION_OP_MULTIPLY
		m.emission = Color(1, 1, 1)
		m.emission_energy_multiplier = 0.35
	_mesh(st, false, m)


## The boards' signs for the director's comparison (fence_look): each [text, board, ink], a sign
## SIGN_PANELS panels long. "sponsor": LED boards with made-up sponsors (placeholders, no real
## brand); "club": the home club's colours and name with the ground's; "plain": none.
func _signs() -> Array:
	match fence_look:
		"sponsor":
			return [["SOUTHERN CROSS HARDWARE", Color(0.85, 0.1, 0.1), Color.WHITE],
					["BLUEGUM BANK", Color(0.05, 0.2, 0.55), Color.WHITE],
					["GOLDFIELDS LAGER", Color(0.95, 0.75, 0.1), Color(0.1, 0.1, 0.1)],
					["COASTLINE INSURANCE", Color(0.0, 0.55, 0.45), Color.WHITE],
					["OUTBACK FUEL", Color(0.12, 0.12, 0.14), Color(1.0, 0.55, 0.1)]]
		"club":
			var nm := home_name.to_upper()
			var gr := ground_name.to_upper()
			return [[nm, home_cols[0], home_cols[1]], [gr, home_cols[1], home_cols[0]]]
	return []


func _sign_text(t: float, text: String, ink: Color) -> void:
	var l := Label3D.new()
	l.text = text
	var f := SystemFont.new()
	f.font_names = PackedStringArray(["Bahnschrift", "Arial"])
	f.font_weight = 700
	l.font = f
	l.font_size = 128
	l.pixel_size = 0.005
	l.modulate = ink
	l.outline_size = 0
	l.shaded = false
	l.double_sided = false
	l.position = _p(t, -0.04, BOARD_H * 0.5)
	# Its face (+Z) toward the field.
	l.basis = Basis.looking_at(Vector3(cos(t) / a, 0.0, sin(t) / b).normalized(), Vector3.UP)
	add_child(l)


## The main camera's platform on each wing (the ground turns for a change of ends, so the camera's
## wing can be either): a deck under the lens, no seats in front of it or under it.
func _platforms(half_wid: float) -> void:
	var off := CAM_BACK - (b - half_wid)
	var deck_y := CAM_UP - 1.6
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(0.2, 0.21, 0.23)
	for s in [-1.0, 1.0]:
		var z: float = s * (b + off)
		clear.append(AABB(Vector3(-DECK_W * 0.5, deck_y - 6.0, minf(z, z - s * 9.0) if s > 0 else z - 3.0),
				Vector3(DECK_W, 30.0, 12.0)))
		var mi := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(DECK_W, 0.4, DECK_D)
		mi.mesh = bm
		mi.material_override = m
		# The deck's front edge 0.6 m ahead of the lens, so its rail sits 45 degrees below
		# the eye line, out of the picture.
		mi.position = Vector3(0.0, deck_y - 0.2, z + s * (DECK_D * 0.5 - 0.6))
		add_child(mi)
		var rail := MeshInstance3D.new()
		var rm := BoxMesh.new()
		rm.size = Vector3(DECK_W, 1.0, 0.1)
		rail.mesh = rm
		rail.material_override = m
		rail.position = Vector3(0.0, deck_y + 0.5, z - s * 0.6)
		add_child(rail)
