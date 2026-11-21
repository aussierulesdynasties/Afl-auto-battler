class_name Oval3DCrowd
extends Node3D
## The 3D view's crowd (row 202 step 2c; director 2026-11-17, Bible 2.92): a stepped concrete
## stand all the way round with a bench on every row and a supporter on most seats, each in his
## own club's colours. The mix: within MIX_D of the camera each supporter is a 3D person
## (Oval3DCrowdSet's baked bodies, seated idle and goal cheer); beyond it he is a card cut from
## the same bodies, turned to face the camera. When a side kicks a goal its supporters rise.
## Looks only: it reads nothing from the match but the time and who kicked the goal.

const CROWD_SET := "res://assets/oval3d/crowd_set.res"
const ROWS := 42
const SEAT := 0.55           # m between neighbours along a row
const AISLE_EVERY := 28      # seats between aisles (an aisle is two seats wide)
const EMPTY := 0.08          # share of seats left empty
const NEUTRAL := 0.12        # share of supporters in neither club's colours
const SECTORS := 96          # chunks round the ground (each also split front rows / back rows)
const SEAT_TIERS := 3        # a real ground's chunks: each sector also split low / middle / high
const MIX_D := 55.0          # m from the camera: 3D people nearer, cards beyond
const BASE_Y := 1.2          # m: the front row's step, level with the fence top
## The bench: SEAT_H high, from SEAT_F to SEAT_B m back from the row's front edge; the
## supporter's origin PERSON_D m back; a card stands CARD_FWD m forward of it (a seated body's
## knees reach forward of its origin). Chosen on the 2c board (2026-11-17).
const SEAT_H := 0.42
const SEAT_F := 0.40
const SEAT_B := 0.80
const PERSON_D := 0.65
const CARD_FWD := 0.5

var supporters := 0
## m from the camera within which a supporter is a 3D person (Oval3DQuality's people_d; MIX_D,
## the ruled mix, at High). 0: every supporter a card, and no 3D people are built at all.
var mix_d := MIX_D
var _people_mats: Array = []
var _card_mat: ShaderMaterial
var _chunks: Array = []      # [{people: [MultiMeshInstance3D per body], cards: MultiMeshInstance3D}]


## The stand round an ellipse a x b m (the fence line), STAND_DEPTH deep, rising to rise_to m,
## and its supporters. home and away are each club's two colours (GameDB.club_colours).
func build(a: float, b: float, depth: float, rise_to: float, home: Array, away: Array) -> void:
	var cs: Oval3DCrowdSet = load(CROWD_SET)
	var pitch := depth / ROWS
	var rise := (rise_to - BASE_Y) / ROWS
	_terrace(a, b, pitch, rise)
	_materials(cs, home, away)
	_seat(cs, a, b, pitch, rise)


## A real ground's crowd (row 202 2b/2c): a supporter on most of the model's own seats, the same
## mix as the stand (3D people within MIX_D, cards beyond), and the same colours and cheer.
## seats are the ground's seat transforms (each seat's origin and turn, in this node's space);
## tmpl the seat's triangles (seat_tmpl.bin), from which sitting_spot finds where he sits.
func build_on_seats(seats: Array, tmpl: PackedVector3Array, home: Array, away: Array) -> void:
	var cs: Oval3DCrowdSet = load(CROWD_SET)
	_materials(cs, home, away)
	var spot := sitting_spot(tmpl)
	var rng := RandomNumberGenerator.new()
	rng.seed = 2026
	var home_share := []
	for s in range(SECTORS):
		home_share.append(rng.randf_range(0.4, 0.8))
	# Tiers by height: the lowest third of the seats, the middle and the top each draw apart, so
	# a near chunk is never a strip from the fence to the roof.
	var ys := PackedFloat32Array()
	for t: Transform3D in seats:
		ys.append(t.origin.y)
	ys.sort()
	var cuts := [ys[ys.size() / 3], ys[ys.size() * 2 / 3]] if ys.size() > 2 else [INF, INF]
	var per := []
	for i in range(SECTORS * SEAT_TIERS):
		per.append([])
	for t: Transform3D in seats:
		if rng.randf() < EMPTY:
			continue
		var at := t * spot
		var th := fposmod(atan2(at.origin.z, at.origin.x), TAU)
		var sector := int(th / TAU * SECTORS) % SECTORS
		var tier := 0 if at.origin.y < cuts[0] else (1 if at.origin.y < cuts[1] else 2)
		per[sector * SEAT_TIERS + tier].append(_supporter(cs, rng, at, home_share[sector]))
	_chunked(cs, per)


## Where a supporter sits on a seat, in the seat's own space, from its triangles: his origin on
## the floor under the seat (its lowest point), PERSON_D - SEAT_F - (SEAT_B - SEAT_F) / 2 behind
## the pan's middle as on the stand, facing out over the pan, away from the backrest.
static func sitting_spot(tmpl: PackedVector3Array) -> Transform3D:
	var lo := INF
	var hi := -INF
	for v in tmpl:
		lo = minf(lo, v.y)
		hi = maxf(hi, v.y)
	# The pan: the points halfway between the floor and the backrest's top; the backrest: the
	# points at its top. Out over the pan, away from the backrest, is the way he faces.
	var pan := Vector3.ZERO
	var n_pan := 0
	var back := Vector3.ZERO
	var n_back := 0
	var pan_y := lo + (hi - lo) * 0.5
	for v in tmpl:
		if absf(v.y - pan_y) < (hi - lo) * 0.06:
			pan += v
			n_pan += 1
		elif v.y > hi - (hi - lo) * 0.06:
			back += v
			n_back += 1
	pan /= maxf(1.0, float(n_pan))
	back /= maxf(1.0, float(n_back))
	var front := Vector3(pan.x - back.x, 0.0, pan.z - back.z)
	front = front.normalized() if front.length() > 0.001 else Vector3.BACK
	# Front to back, the pan's middle is halfway between its front edge and its back edge.
	var near := INF
	var far := -INF
	for v in tmpl:
		if absf(v.y - pan_y) < (hi - lo) * 0.06:
			near = minf(near, v.dot(front))
			far = maxf(far, v.dot(front))
	if near < far:
		pan += front * ((near + far) * 0.5 - pan.dot(front))
	var behind := PERSON_D - (SEAT_F + SEAT_B) * 0.5
	var origin := Vector3(pan.x, lo, pan.z) - front * behind
	# The bodies face +Z (the stand turns them with looking_at the way out, -Z).
	return Transform3D(Basis.looking_at(-front, Vector3.UP), origin)


func _materials(cs: Oval3DCrowdSet, home: Array, away: Array) -> void:
	for body: Dictionary in cs.bodies:
		var pm := ShaderMaterial.new()
		pm.shader = preload("res://scripts/ui/match/oval3d_crowd_people.gdshader")
		pm.set_shader_parameter("pos_tex", body["pos_tex"])
		pm.set_shader_parameter("nrm_tex", body["nrm_tex"])
		pm.set_shader_parameter("fps", float(body["fps"]))
		pm.set_shader_parameter("idle0", body["idle"])
		pm.set_shader_parameter("n_idle", 1)
		pm.set_shader_parameter("cheer", body["cheer"])
		pm.set_shader_parameter("cheer_len", cs.cheer_s + 1.0)
		_colours(pm, home, away)
		_people_mats.append(pm)
	_card_mat = ShaderMaterial.new()
	_card_mat.shader = preload("res://scripts/ui/match/oval3d_crowd_card.gdshader")
	_card_mat.set_shader_parameter("atlas", cs.atlas)
	_card_mat.set_shader_parameter("bodies", float(cs.bodies.size()))
	_card_mat.set_shader_parameter("card_w", cs.card_w)
	_card_mat.set_shader_parameter("card_h", cs.card_h)
	_card_mat.set_shader_parameter("card_x0", cs.card_x0)
	_card_mat.set_shader_parameter("card_y0", cs.card_y0)
	_card_mat.set_shader_parameter("card_fwd", CARD_FWD)
	# The atlas's own light averages about three-quarters on the lit front; the stand lights it again.
	_card_mat.set_shader_parameter("shade_lift", 1.0 / 0.75)
	_card_mat.set_shader_parameter("cheer_dur", cs.cheer_s)
	_card_mat.set_shader_parameter("cheer_len", cs.cheer_s + 1.0)
	_colours(_card_mat, home, away)


## The match clock (s), which every supporter's idle and cheer run on.
func set_now(t: float) -> void:
	for m: ShaderMaterial in _people_mats + [_card_mat]:
		m.set_shader_parameter("now", t)


## A goal at time t (s): side 0 (home) or 1 (away)'s supporters cheer.
func cheer(side: int, t: float) -> void:
	for m: ShaderMaterial in _people_mats + [_card_mat]:
		m.set_shader_parameter("cheer_from", t)
		m.set_shader_parameter("cheer_side", float(side))


func _colours(m: ShaderMaterial, home: Array, away: Array) -> void:
	m.set_shader_parameter("home_a", home[0])
	m.set_shader_parameter("home_b", home[1])
	m.set_shader_parameter("away_a", away[0])
	m.set_shader_parameter("away_b", away[1])


## A supporter on each seat, row by row, evenly spaced round each row's ellipse, aisles and a few
## empty seats left. Each sector leans to one club (40-80% home); a few wear neither.
func _seat(cs: Oval3DCrowdSet, a0: float, b0: float, pitch: float, rise: float) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 2026
	var home_share := []
	for s in range(SECTORS):
		home_share.append(rng.randf_range(0.4, 0.8))
	var per := []
	for i in range(SECTORS * 2):
		per.append([])
	for r in range(ROWS):
		var dd := float(r) * pitch + PERSON_D
		var y := BASE_Y + float(r + 1) * rise
		var a := a0 + dd
		var b := b0 + dd
		# Arc length round this row's ellipse, so seats sit evenly spaced.
		var N := 4096
		var acc := PackedFloat32Array()
		acc.resize(N + 1)
		var prev := Vector2(a, 0.0)
		for i in range(1, N + 1):
			var th := TAU * float(i) / N
			var p := Vector2(a * cos(th), b * sin(th))
			acc[i] = acc[i - 1] + p.distance_to(prev)
			prev = p
		var L := acc[N]
		var n := int(L / SEAT)
		var j := 0
		for k in range(n):
			if k % AISLE_EVERY < 2 or rng.randf() < EMPTY:
				continue
			var at := (float(k) + (0.5 if r % 2 == 1 else 0.0)) * L / n
			while j < N and acc[j + 1] < at:
				j += 1
			var th := TAU * (float(j) + (at - acc[j]) / maxf(0.0001, acc[j + 1] - acc[j])) / N
			var pos := Vector3(a * cos(th), y, b * sin(th))
			var outward := Vector3(cos(th) / a, 0.0, sin(th) / b).normalized()
			var sector := int(th / TAU * SECTORS) % SECTORS
			per[sector * 2 + (0 if r < ROWS / 2 else 1)].append(_supporter(cs, rng,
					Transform3D(Basis.looking_at(outward, Vector3.UP), pos), home_share[sector]))
	_chunked(cs, per)


## One supporter at a seat's spot: turned a touch and sized a little either way, in his club's
## colours (most of a sector lean to the home side, a few to neither), on a body picked by share.
func _supporter(cs: Oval3DCrowdSet, rng: RandomNumberGenerator, at: Transform3D, home_share: float) -> Array:
	var basis := Basis(Vector3.UP, rng.randf_range(-0.2, 0.2)) * at.basis
	basis = basis.scaled(Vector3.ONE * rng.randf_range(0.92, 1.06))
	var side := 0.5 if rng.randf() < NEUTRAL else (0.0 if rng.randf() < home_share else 1.0)
	var wsum := 0.0
	for body: Dictionary in cs.bodies:
		wsum += float(body["share"])
	var pick := rng.randf() * wsum
	var bi := 0
	while bi < cs.bodies.size() - 1 and pick >= float(cs.bodies[bi]["share"]):
		pick -= float(cs.bodies[bi]["share"])
		bi += 1
	supporters += 1
	return [Transform3D(basis, at.origin), Color(rng.randf(), side, rng.randf(), rng.randf()), bi]


## Each chunk of seats as its draws: 3D people (one batch per body, each body has its own
## table) shown within mix_d, and cards (every body in one batch, the body's atlas row in the
## seat's fourth number) beyond.
func _chunked(cs: Oval3DCrowdSet, per: Array) -> void:
	var card := _card_mesh()
	for list: Array in per:
		if list.is_empty():
			continue
		var chunk := {"people": []}
		if mix_d > 0.0:
			for bi in range(cs.bodies.size()):
				var mine: Array = list.filter(func(e): return e[2] == bi)
				var p := _batch(cs.bodies[bi]["mesh"], _people_mats[bi], mine, -1)
				p.visibility_range_end = mix_d
				chunk["people"].append(p)
		var c := _batch(card, _card_mat, list, cs.bodies.size())
		c.visibility_range_begin = mix_d
		chunk["cards"] = c
		_chunks.append(chunk)


## One draw: these seats as a batch of mesh. n_bodies >= 0 puts each seat's body in its fourth number.
func _batch(mesh: Mesh, mat: Material, seats: Array, n_bodies: int) -> MultiMeshInstance3D:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = mesh
	mm.instance_count = seats.size()
	for i in range(seats.size()):
		mm.set_instance_transform(i, seats[i][0])
		var c: Color = seats[i][1]
		if n_bodies >= 0:
			c.a = (float(seats[i][2]) + 0.5) / float(n_bodies)
		mm.set_instance_custom_data(i, c)
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	mmi.material_override = mat
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mmi)
	return mmi


## A card: a 1 x 1 quad standing on its bottom edge (the shader sizes and turns it).
func _card_mesh() -> ArrayMesh:
	var card := ArrayMesh.new()
	var ca := []
	ca.resize(Mesh.ARRAY_MAX)
	ca[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3(-0.5, 0, 0), Vector3(-0.5, 1, 0), Vector3(0.5, 1, 0), Vector3(0.5, 0, 0)])
	ca[Mesh.ARRAY_NORMAL] = PackedVector3Array([Vector3.BACK, Vector3.BACK, Vector3.BACK, Vector3.BACK])
	ca[Mesh.ARRAY_TEX_UV] = PackedVector2Array([Vector2(0, 1), Vector2(0, 0), Vector2(1, 0), Vector2(1, 1)])
	ca[Mesh.ARRAY_INDEX] = PackedInt32Array([0, 1, 2, 0, 2, 3])
	card.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, ca)
	card.custom_aabb = AABB(Vector3(-1.5, -0.5, -1.5), Vector3(3, 3, 3))
	return card


## Concrete steps: each row a riser and a tread, and a bench along it.
func _terrace(semi_a: float, semi_b: float, pitch: float, rise: float) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var seg := 240
	var riser := Color(0.42, 0.42, 0.43)
	var tread := Color(0.2, 0.21, 0.24)
	var seat := Color(0.28, 0.3, 0.36)
	var P := func(t: float, d: float, y: float) -> Vector3:
		return Vector3(cos(t) * (semi_a + d), y, sin(t) * (semi_b + d))
	for i in range(seg):
		var t0 := TAU * float(i) / seg
		var t1 := TAU * float(i + 1) / seg
		var inward := -Vector3(cos(t0) / semi_a, 0.0, sin(t0) / semi_b).normalized()
		for r in range(ROWS):
			var d0 := float(r) * pitch
			var d1 := d0 + pitch
			var y0 := BASE_Y + float(r) * rise
			var y1 := y0 + rise
			_quad(st, [P.call(t0, d0, y0), P.call(t0, d0, y1), P.call(t1, d0, y1), P.call(t1, d0, y0)], inward, riser)
			_quad(st, [P.call(t0, d0, y1), P.call(t0, d1, y1), P.call(t1, d1, y1), P.call(t1, d0, y1)], Vector3.UP, tread)
			var sf := d0 + SEAT_F
			var sb := d0 + SEAT_B
			var ys := y1 + SEAT_H
			_quad(st, [P.call(t0, sf, y1), P.call(t0, sf, ys), P.call(t1, sf, ys), P.call(t1, sf, y1)], inward, seat)
			_quad(st, [P.call(t0, sf, ys), P.call(t0, sb, ys), P.call(t1, sb, ys), P.call(t1, sf, ys)], Vector3.UP, seat)
	var m := StandardMaterial3D.new()
	m.vertex_color_use_as_albedo = true
	m.vertex_color_is_srgb = true
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.roughness = 1.0
	var mi := MeshInstance3D.new()
	mi.name = "Terrace"
	mi.mesh = st.commit()
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)


func _quad(st: SurfaceTool, q: Array, n: Vector3, c: Color) -> void:
	for k in [0, 1, 2, 0, 2, 3]:
		st.set_normal(n)
		st.set_color(c)
		st.add_vertex(q[k])
