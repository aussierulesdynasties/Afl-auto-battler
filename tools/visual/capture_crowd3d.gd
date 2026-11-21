extends "res://tools/visual/capture_look3d.gd"
## PROTOTYPE (row 202, 3D view plan step 2c): the crowd's methods side by side, for the director
## to choose between (the freeze: nothing here is the game's crowd until he picks).
##   godot --path . --script tools/visual/capture_crowd3d.gd -- OUTDIR METHODS VATDIR [stills|goal]
## METHODS is a comma list of:
##   painted  today's stand: people painted on the slope as coloured blobs
##   people   every seat holds a low-poly 3D supporter, moving (a baked vertex animation)
##   cards    every seat holds a flat picture of that supporter that turns to the camera
##   mix      3D supporters near the camera, cards beyond MIXD metres (55 by default)
##   game     the game's own crowd as Oval3D builds it (Oval3DCrowd, the chosen mix): nothing added
## VATDIR is a crowd bake (meta.json, mesh.bin, pos.bin, nrm.bin), or a comma list of bakes, each
## with its share of the seats (dir=0.3,dir=0.2,...; no share = 1): every seat takes one body.
## IDLE=a,b names the idle clips, CHEER=c the goal cheer (default: the first clip and the last).
## stills: the same wing moment as capture_look3d, from the phone, wide and close cameras, and
## each method's cost on this PC (GPU ms, triangles, draw calls). goal: from 3 s before the
## match's first goal for 7 s, every frame from the phone camera under each method, so each
## method's reaction can be watched.
## Look: run with LOOK=sky+agxtv EXPO=3.056 CROWD=0.58 for the approved fine day; SKYVIEW=1 adds the
## view from the far wing across to the sun-side stand (the most crowd in one frame).
## A seated crowd: SEAT_H=0.45 adds a bench on each row (SEAT_FB=front,back m from the row's edge),
## PERSON_D=m sets where each supporter's origin stands on the tread.

const ROWS := 42
const SEAT := 0.55           # m between neighbours along a row
const AISLE_EVERY := 28      # seats between aisles (an aisle is two seats wide)
const EMPTY := 0.08          # share of seats left empty
const SECTORS := 96
const CELL := Vector2i(64, 128)
const GOAL_BEFORE := 3.0
const GOAL_LEN := 7.0

var _goal_t := -1.0
var _goal_side := 0
var _chunks := []
var _people_mats := []
var _card_mat: ShaderMaterial
var _terrace: MeshInstance3D
var _mixd := 55.0
# A seated crowd sits on a bench along each row: its top SEAT_H m above the tread, from SEAT_F to
# SEAT_B m back from the row's front edge (0 = standing crowd, no bench).
var _seat_h := 0.0
var _seat_f := 0.35
var _seat_b := 0.75
# Where a supporter's origin stands, m back from the row's front edge (-1 = mid-tread).
var _person_d := -1.0
var _cost := {}


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	var methods := str(args[1]).split(",")
	var vat_dir := str(args[2])
	var mode := str(args[3]) if args.size() > 3 else "stills"
	var look := OS.get_environment("LOOK") if OS.get_environment("LOOK") != "" else "sky+agxtv"
	if OS.get_environment("MIXD") != "":
		_mixd = float(OS.get_environment("MIXD"))
	if OS.get_environment("SEAT_H") != "":
		_seat_h = float(OS.get_environment("SEAT_H"))
		var fb := OS.get_environment("SEAT_FB").split(",")
		if fb.size() == 2:
			_seat_f = float(fb[0])
			_seat_b = float(fb[1])
	if OS.get_environment("PERSON_D") != "":
		_person_d = float(OS.get_environment("PERSON_D"))
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	var res: Dictionary = Sim.new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), 31).run()
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.use_debanding = true
	_size(SIZE)
	# Pass 1, the log: the wing moment (as capture_look3d) and the first goal, its time and side.
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	var played := 0.0
	var want := -1.0
	var best := 0
	while played < MAX_T:
		d.advance(DT)
		oval.sync(DT)
		oval.aim_end(UP, BACK)
		played += DT
		if played < 6.0:
			continue
		if _goal_t < 0.0 and not d.flash.is_empty() and bool(d.flash.get("goal", false)):
			_goal_t = played
			_goal_side = int((d.events[d.emitted - 1] as Dictionary).get("side", 0))
		var b: Vector3 = oval.ball.global_position
		if absf(b.z) > WING_Z and absf(b.x) < MID_X:
			var n := _in_view(oval)
			if n > best:
				best = n
				want = played
				_wing_sign = signf(b.z)
	oval.queue_free()
	await process_frame
	print("GOAL at %.2f s, side %d; wing moment %.2f s" % [_goal_t, _goal_side, want])
	var start := want if mode == "stills" else _goal_t - GOAL_BEFORE
	# Pass 2: the same match again, drawn, to that moment.
	d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	played = 0.0
	while played < start - DT * 0.5:
		d.advance(DT)
		oval.sync(DT)
		oval.aim_end(UP, BACK)
		played += DT
		await process_frame
	var fn := FastNoiseLite.new()
	fn.noise_type = FastNoiseLite.TYPE_PERLIN
	fn.fractal_type = FastNoiseLite.FRACTAL_FBM
	fn.fractal_octaves = 5
	fn.frequency = 0.008
	fn.seed = 7
	_clouds = NoiseTexture2D.new()
	_clouds.width = 512
	_clouds.height = 512
	_clouds.seamless = true
	_clouds.generate_mipmaps = true
	_clouds.noise = fn
	await _clouds.changed
	var t0 := Time.get_ticks_msec()
	if methods != PackedStringArray(["game"]):
		await _build_crowd(oval, vat_dir, gdb)
	print("CROWD built in %.1f s" % ((Time.get_ticks_msec() - t0) / 1000.0))
	_reset(oval, "perfect", "day")
	for part in look.split("+"):
		_apply(oval, part)
	await _match_exposure(oval)
	_sky_view(oval)
	if _card_mat != null:
		_set_now(played)
	if mode == "stills":
		for m in methods:
			_method(oval, m)
			var cams := ["phone", "wide", "close"]
			if OS.get_environment("SKYVIEW") == "1":
				cams.append("sky")
			if OS.get_environment("STANDVIEW") == "1":
				cams.append("stand")
			for cam in cams:
				_size(WIDE if cam in ["wide", "sky", "stand"] else SIZE)
				if cam == "phone":
					oval.aim_end(UP, BACK)
				elif cam == "wide":
					oval.aim_wing(UP, BACK * 1.3)
				elif cam == "sky":
					_aim_sky(oval)
				elif cam == "stand":
					_aim_stand(oval)
				else:
					oval.aim_close()
				for i in range(3):
					await process_frame
				await _save(oval, out, "crowd_%s_%s" % [m, cam])
				await _measure(m + "_" + cam)
		var f := FileAccess.open(out.path_join("cost.json"), FileAccess.WRITE)
		f.store_string(JSON.stringify(_cost, " "))
	else:
		_size(SIZE)
		for m in methods:
			DirAccess.make_dir_recursive_absolute(out.path_join("goal_" + m))
		var n := int(GOAL_LEN / DT)
		for k in range(n):
			d.advance(DT)
			oval.sync(DT)
			oval.aim_end(UP, BACK)
			played += DT
			if _card_mat != null:
				_set_now(played)
			for m in methods:
				_method(oval, m)
				await process_frame
				await RenderingServer.frame_post_draw
				root.get_viewport().get_texture().get_image().save_png(
						out.path_join("goal_%s/f_%04d.png" % [m, k]))
		print("GOAL frames %d per method" % n)
	quit()


func _set_now(t: float) -> void:
	for m in _people_mats + [_card_mat]:
		m.set_shader_parameter("now", t)
		m.set_shader_parameter("cheer_from", _goal_t)
		m.set_shader_parameter("cheer_side", float(_goal_side))


## One method on show: today's painted slope, or the stepped stand with people, cards or both.
func _method(oval, m: String) -> void:
	oval.crowd.visible = m == "game"
	if m == "game":
		return
	for c in _crowds(oval):
		c.visible = m == "painted"
	_terrace.visible = m != "painted"
	for ch in _chunks:
		for p: MultiMeshInstance3D in ch["people"]:
			p.visible = m == "people" or m == "mix"
			p.visibility_range_end = _mixd if m == "mix" else 0.0
		var c: MultiMeshInstance3D = ch["cards"]
		c.visible = m == "cards" or m == "mix"
		c.visibility_range_begin = _mixd if m == "mix" else 0.0


## This PC's cost of the frame on screen: GPU and CPU time averaged over 30 frames, triangles and
## draw calls (the phone's cost is measured later, on a phone).
func _measure(label: String) -> void:
	var rid := root.get_viewport_rid()
	RenderingServer.viewport_set_measure_render_time(rid, true)
	for i in range(10):
		await process_frame
	var g := 0.0
	var c := 0.0
	for i in range(30):
		await RenderingServer.frame_post_draw
		g += RenderingServer.viewport_get_measured_render_time_gpu(rid)
		c += RenderingServer.viewport_get_measured_render_time_cpu(rid)
	var prims := int(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME))
	var draws := int(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
	_cost[label] = {"gpu_ms": g / 30.0, "cpu_ms": c / 30.0, "tris": prims, "draws": draws}
	print("COST %-16s gpu %6.2f ms  cpu %5.2f ms  tris %9d  draws %4d" % [label, g / 30.0, c / 30.0, prims, draws])


func _build_crowd(oval, vat_spec: String, gdb) -> void:
	var bodies := []
	var weights := PackedFloat32Array()
	for part in vat_spec.split(","):
		var kv := part.split("=")
		bodies.append(_load_body(kv[0], gdb))
		weights.append(float(kv[1]) if kv.size() > 1 else 1.0)
	# One frame for every body's pictures, so a child's card stands shorter than a man's.
	var mn: Vector3 = bodies[0]["mn"]
	var mx: Vector3 = bodies[0]["mx"]
	for b in bodies:
		mn = mn.min(b["mn"])
		mx = mx.max(b["mx"])
	# The cards' atlas: each body drawn from the front, slightly above, eight frames of its first
	# idle and eight of its cheer, one body to an atlas row.
	var tall := (mx.y - mn.y) * 1.06
	var cx := (mn.x + mx.x) * 0.5
	var cy := (mn.y + mx.y) * 0.5
	var vp := SubViewport.new()
	vp.size = CELL
	vp.transparent_bg = true
	vp.own_world_3d = true
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(vp)
	var mi := MeshInstance3D.new()
	vp.add_child(mi)
	var cam := Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.size = tall
	vp.add_child(cam)
	var e := deg_to_rad(10.0)
	cam.position = Vector3(cx, cy, 0.0) + Vector3(0.0, sin(e), cos(e)) * 10.0
	cam.look_at(Vector3(cx, cy, 0.0), Vector3.UP)
	cam.current = true
	var atlas := Image.create(CELL.x * 16, CELL.y * bodies.size(), false, Image.FORMAT_RGBA8)
	for bi in range(bodies.size()):
		var b: Dictionary = bodies[bi]
		mi.mesh = b["mesh"]
		var am: ShaderMaterial = (b["mat"] as ShaderMaterial).duplicate()
		am.set_shader_parameter("mode", 1)
		mi.material_override = am
		for col in range(16):
			var c: Dictionary = b["idle"] if col < 8 else b["cheer"]
			var row := int(c["row"]) + int(floor(float(col % 8) * float(c["frames"]) / 8.0))
			am.set_shader_parameter("atlas_row", row)
			for w in range(2):
				await process_frame
			await RenderingServer.frame_post_draw
			var img := vp.get_texture().get_image()
			img.convert(Image.FORMAT_RGBA8)
			atlas.blit_rect(img, Rect2i(Vector2i.ZERO, CELL), Vector2i(col * CELL.x, bi * CELL.y))
	vp.queue_free()
	atlas.save_png("user://crowd3d_atlas.png")
	atlas.generate_mipmaps()
	var ch: Dictionary = bodies[0]["cheer"]
	var pm: ShaderMaterial = bodies[0]["mat"]
	_card_mat = ShaderMaterial.new()
	_card_mat.shader = load("res://scripts/ui/match/oval3d_crowd_card.gdshader")
	var cm := _card_mat
	cm.set_shader_parameter("atlas", ImageTexture.create_from_image(atlas))
	cm.set_shader_parameter("bodies", float(bodies.size()))
	cm.set_shader_parameter("card_w", tall * 0.5)
	cm.set_shader_parameter("card_h", tall)
	cm.set_shader_parameter("card_x0", cx)
	cm.set_shader_parameter("card_y0", cy - tall * 0.5)
	# A seated body's knees reach forward of its origin: CARD_FWD=m stands the picture there.
	cm.set_shader_parameter("card_fwd", float(OS.get_environment("CARD_FWD")) if OS.get_environment("CARD_FWD") != "" else 0.0)
	# The atlas's own light averages about three-quarters on the lit front; the stand lights it again.
	cm.set_shader_parameter("shade_lift", 1.0 / 0.75)
	cm.set_shader_parameter("cheer_dur", float(ch["frames"]) / float(ch["fps"]))
	cm.set_shader_parameter("cheer_len", float(ch["frames"]) / float(ch["fps"]) + 1.0)
	for k in ["home_a", "home_b", "away_a", "away_b"]:
		cm.set_shader_parameter(k, pm.get_shader_parameter(k))
	var card := ArrayMesh.new()
	var ca := []
	ca.resize(Mesh.ARRAY_MAX)
	ca[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3(-0.5, 0, 0), Vector3(-0.5, 1, 0), Vector3(0.5, 1, 0), Vector3(0.5, 0, 0)])
	ca[Mesh.ARRAY_NORMAL] = PackedVector3Array([Vector3.BACK, Vector3.BACK, Vector3.BACK, Vector3.BACK])
	ca[Mesh.ARRAY_TEX_UV] = PackedVector2Array([Vector2(0, 1), Vector2(0, 0), Vector2(1, 0), Vector2(1, 1)])
	ca[Mesh.ARRAY_INDEX] = PackedInt32Array([0, 1, 2, 0, 2, 3])
	card.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, ca)
	card.custom_aabb = AABB(Vector3(-1.5, -0.5, -1.5), Vector3(3, 3, 3))
	_seat_crowd(oval, bodies, weights, card)


## One baked body: its mesh (each vertex's column and part), its own 3D-people material, its frame.
func _load_body(vat_dir: String, gdb) -> Dictionary:
	var meta: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(vat_dir.path_join("meta.json")))
	var f := FileAccess.open(vat_dir.path_join("mesh.bin"), FileAccess.READ)
	var nv := f.get_32()
	var ni := f.get_32()
	var roles := f.get_buffer(nv * 4)
	var idx := f.get_buffer(ni * 4).to_int32_array()
	# Blender's front faces wind anticlockwise, Godot's clockwise.
	for t in range(0, ni, 3):
		var k := idx[t + 1]
		idx[t + 1] = idx[t + 2]
		idx[t + 2] = k
	var rows := int(meta["rows"])
	var pb := FileAccess.get_file_as_bytes(vat_dir.path_join("pos.bin"))
	var nb := FileAccess.get_file_as_bytes(vat_dir.path_join("nrm.bin"))
	var pos_tex := ImageTexture.create_from_image(Image.create_from_data(nv, rows, false, Image.FORMAT_RGBF, pb))
	var nrm_tex := ImageTexture.create_from_image(Image.create_from_data(nv, rows, false, Image.FORMAT_RGBF, nb))
	var p0 := pb.slice(0, nv * 12).to_float32_array()
	var n0 := nb.slice(0, nv * 12).to_float32_array()
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	var uvs := PackedVector2Array()
	var cols := PackedColorArray()
	for i in range(nv):
		verts.append(Vector3(p0[i * 3], p0[i * 3 + 1], p0[i * 3 + 2]))
		norms.append(Vector3(n0[i * 3], n0[i * 3 + 1], n0[i * 3 + 2]))
		uvs.append(Vector2(float(i) + 0.5, 0.0))
		cols.append(Color(roles[i * 4] / 255.0, roles[i * 4 + 1] / 255.0, roles[i * 4 + 2] / 255.0, roles[i * 4 + 3] / 255.0))
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_NORMAL] = norms
	arr[Mesh.ARRAY_TEX_UV] = uvs
	arr[Mesh.ARRAY_COLOR] = cols
	arr[Mesh.ARRAY_INDEX] = idx
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var mn := Vector3(meta["min"][0], meta["min"][1], meta["min"][2])
	var mx := Vector3(meta["max"][0], meta["max"][1], meta["max"][2])
	mesh.custom_aabb = AABB(mn - Vector3.ONE * 0.3, mx - mn + Vector3.ONE * 0.6)
	# The clips: which rows are the idles and which the cheer.
	var clips := {}
	for c in meta["clips"]:
		clips[str(c["name"])] = c
	var names: Array = meta["clips"].map(func(c): return str(c["name"]))
	var idle_names: Array = Array(OS.get_environment("IDLE").split(",")) if OS.get_environment("IDLE") != "" else [names[0]]
	var cheer_name := OS.get_environment("CHEER") if OS.get_environment("CHEER") != "" else str(names[-1])
	var hc: Array = gdb.club_colours("FRE")
	var ac: Array = gdb.club_colours("STK")
	var pm := ShaderMaterial.new()
	pm.shader = load("res://scripts/ui/match/oval3d_crowd_people.gdshader")
	pm.set_shader_parameter("pos_tex", pos_tex)
	pm.set_shader_parameter("nrm_tex", nrm_tex)
	pm.set_shader_parameter("fps", float(meta["clips"][0]["fps"]))
	for i in range(mini(4, idle_names.size())):
		var c: Dictionary = clips[idle_names[i]]
		pm.set_shader_parameter("idle%d" % i, Vector2i(int(c["row"]), int(c["frames"])))
	pm.set_shader_parameter("n_idle", mini(4, idle_names.size()))
	var ch: Dictionary = clips[cheer_name]
	pm.set_shader_parameter("cheer", Vector2i(int(ch["row"]), int(ch["frames"])))
	pm.set_shader_parameter("cheer_len", float(ch["frames"]) / float(ch["fps"]) + 1.0)
	for k in ["home_a", "home_b", "away_a", "away_b"]:
		var src: Array = hc if k.begins_with("home") else ac
		pm.set_shader_parameter(k, src[0] if k.ends_with("_a") else src[1])
	_people_mats.append(pm)
	print("BODY %s: %d verts, %d tris, %.2f m tall" % [vat_dir.get_file(), nv, ni / 3, mx.y - mn.y])
	return {"mesh": mesh, "mat": pm, "mn": mn, "mx": mx, "idle": clips[idle_names[0]], "cheer": ch}


## The stepped stand (ROWS rows up the same slope as today's stand) and a supporter on each seat,
## split into chunks round the ground and front/back so the far ones can drop to cards.
func _seat_crowd(oval, bodies: Array, weights: PackedFloat32Array, card: Mesh) -> void:
	var O = oval.get_script()
	var A: float = MatchMotion.HALF_LEN + O.FENCE
	var B: float = MatchMotion.HALF_WID + O.FENCE
	var pitch: float = O.STAND_DEPTH / ROWS
	var rise: float = (O.STAND_RISE - 1.2) / ROWS
	_terrace_mesh(oval, A, B, pitch, rise)
	var rng := RandomNumberGenerator.new()
	rng.seed = 2026
	var home_share := []
	for s in range(SECTORS):
		home_share.append(rng.randf_range(0.4, 0.8))
	var per := []
	for i in range(SECTORS * 2):
		per.append([])
	var total := 0
	var wsum := 0.0
	for w in weights:
		wsum += w
	var counts := PackedInt32Array()
	counts.resize(bodies.size())
	for r in range(ROWS):
		var dd := float(r) * pitch + (_person_d if _person_d >= 0.0 else 0.5 * pitch)
		var y := 1.2 + float(r + 1) * rise
		var a := A + dd
		var b := B + dd
		# Arc length round this row's ellipse, so seats sit evenly spaced.
		var N := 4096
		var acc := PackedFloat32Array()
		acc.resize(N + 1)
		acc[0] = 0.0
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
			var basis := Basis(Vector3.UP, rng.randf_range(-0.2, 0.2)) * Basis.looking_at(outward, Vector3.UP)
			basis = basis.scaled(Vector3.ONE * rng.randf_range(0.92, 1.06))
			var sector := int(th / TAU * SECTORS) % SECTORS
			var u := rng.randf()
			var side := 0.5 if u < 0.12 else (0.0 if rng.randf() < home_share[sector] else 1.0)
			var pick := rng.randf() * wsum
			var bi := 0
			while bi < bodies.size() - 1 and pick >= weights[bi]:
				pick -= weights[bi]
				bi += 1
			counts[bi] += 1
			per[sector * 2 + (0 if r < ROWS / 2 else 1)].append(
					[Transform3D(basis, pos), Color(rng.randf(), side, rng.randf(), rng.randf()), bi])
			total += 1
	for list in per:
		var chunk := {"people": []}
		# 3D people: one batch per body (each body has its own table). Cards: every body in one
		# batch, the body's atlas row in the seat's fourth number.
		for bi in range(bodies.size()):
			var mine: Array = list.filter(func(e): return e[2] == bi)
			chunk["people"].append(_batch(oval, bodies[bi]["mesh"], bodies[bi]["mat"], mine, -1))
		chunk["cards"] = _batch(oval, card, _card_mat, list, bodies.size())
		_chunks.append(chunk)
	print("SEATS %d supporters in %d chunks, by body %s" % [total, _chunks.size(), counts])


## One draw: these seats as a batch of mesh. n_bodies >= 0 puts each seat's body in its fourth number.
func _batch(oval, mesh: Mesh, mat: Material, seats: Array, n_bodies: int) -> MultiMeshInstance3D:
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
	mmi.visible = false
	oval.add_child(mmi)
	return mmi


## Concrete steps: each row a riser and a tread, between the fence and today's stand's top.
func _terrace_mesh(oval, semi_a: float, semi_b: float, pitch: float, rise: float) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var seg := 240
	var riser := Color(0.42, 0.42, 0.43)
	var tread := Color(0.2, 0.21, 0.24)
	var seat := Color(0.28, 0.3, 0.36)
	for i in range(seg):
		var t0 := TAU * float(i) / seg
		var t1 := TAU * float(i + 1) / seg
		for r in range(ROWS):
			var d0 := float(r) * pitch
			var d1 := d0 + pitch
			var y0 := 1.2 + float(r) * rise
			var y1 := y0 + rise
			var P := func(t: float, d: float, y: float) -> Vector3:
				return Vector3(cos(t) * (semi_a + d), y, sin(t) * (semi_b + d))
			var inward := -Vector3(cos(t0) / semi_a, 0.0, sin(t0) / semi_b).normalized()
			_quad(st, [P.call(t0, d0, y0), P.call(t0, d0, y1), P.call(t1, d0, y1), P.call(t1, d0, y0)], inward, riser)
			_quad(st, [P.call(t0, d0, y1), P.call(t0, d1, y1), P.call(t1, d1, y1), P.call(t1, d0, y1)], Vector3.UP, tread)
			if _seat_h > 0.0:
				var sf := d0 + _seat_f
				var sb := d0 + _seat_b
				var ys := y1 + _seat_h
				_quad(st, [P.call(t0, sf, y1), P.call(t0, sf, ys), P.call(t1, sf, ys), P.call(t1, sf, y1)], inward, seat)
				_quad(st, [P.call(t0, sf, ys), P.call(t0, sb, ys), P.call(t1, sb, ys), P.call(t1, sf, ys)], Vector3.UP, seat)
	var m := StandardMaterial3D.new()
	m.vertex_color_use_as_albedo = true
	m.vertex_color_is_srgb = true
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.roughness = 1.0
	_terrace = MeshInstance3D.new()
	_terrace.mesh = st.commit()
	_terrace.material_override = m
	_terrace.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_terrace.visible = false
	oval.add_child(_terrace)


func _quad(st: SurfaceTool, q: Array, n: Vector3, c: Color) -> void:
	for k in [0, 1, 2, 0, 2, 3]:
		st.set_normal(n)
		st.set_color(c)
		st.add_vertex(q[k])


## A self-check view, not a game camera: from the fence, 10 m off the sun-side stand's first rows,
## a little to one side, so a dozen seated supporters fill the frame (pose, bench, clipping).
func _aim_stand(oval) -> void:
	var O = oval.get_script()
	var A: float = MatchMotion.HALF_LEN + O.FENCE
	var B: float = MatchMotion.HALF_WID + O.FENCE
	var rise: float = (O.STAND_RISE - 1.2) / ROWS
	var to_sun: Vector3 = oval._sun.global_basis.z
	var th := atan2(to_sun.z / B, to_sun.x / A)
	var P := func(t: float, d: float, y: float) -> Vector3:
		return Vector3(cos(t) * (A + d), y, sin(t) * (B + d))
	var cam: Camera3D = oval.camera
	cam.global_position = P.call(th - 0.06, -7.0, 4.0)
	cam.look_at(P.call(th, 3.0, 1.2 + 4.0 * rise + 0.7), Vector3.UP)
