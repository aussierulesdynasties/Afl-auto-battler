extends "res://tools/visual/capture_look3d.gd"
## PROTOTYPE (row 202, close-up supporters): one candidate supporter in our stand, filmed from the
## row behind with the ground beyond (the director's shot: "a supporter's head and shoulders in
## the foreground"). Nothing here is the game's until he picks it.
##   godot --path . --script tools/visual/capture_closeup3d.gd -- OUTDIR FIGURE.glb CLIP HEIGHT_M [FRAMES]
## FIGURE: a GLB (res:// or an absolute path) with CLIP among its animations. HEIGHT_M: his standing
## height. FRAMES: frames to film at 24 fps (1 = a still).
## The match moment: 2 s after the first goal of the seeded Fremantle v St Kilda match (a break in play).
## Env: ROW (default 8) the supporter's row; SIDE (default 0.45) m the camera sits off his right
## shoulder; BACK (default 1.25) m behind him; EYE (default 1.62) camera height over his tread;
## FOV (default 50); TURN (default 0) deg the camera looks away from straight across the ground.

const AFTER_GOAL := 2.0


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	var fig_path := str(args[1])
	var clip := str(args[2])
	var height := float(args[3])
	var frames := int(args[4]) if args.size() > 4 else 1
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	var res: Dictionary = Sim.new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), 31).run()
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.use_debanding = true
	_size(WIDE)
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	var played := 0.0
	var goal_t := -1.0
	while played < MAX_T:
		d.advance(DT)
		oval.sync(DT)
		oval.aim_end(UP, BACK)
		played += DT
		if goal_t < 0.0 and played > 6.0 and not d.flash.is_empty() and bool(d.flash.get("goal", false)):
			goal_t = played
		if goal_t >= 0.0 and played >= goal_t + AFTER_GOAL:
			break
		await process_frame
	print("CLOSEUP goal at %.2f s, filming from %.2f s" % [goal_t, played])
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
	_reset(oval, "perfect", "day")
	for part in ["sky", "agxtv"]:
		_apply(oval, part)
	await _match_exposure(oval)
	# The seat: ROW rows up the stand on the wing nearest the play, square to the centre line.
	var O = oval.get_script()
	var C = Oval3DCrowd
	var pitch: float = O.STAND_DEPTH / C.ROWS
	var rise: float = (O.STAND_RISE - C.BASE_Y) / C.ROWS
	var row := int(_env("ROW", 8.0))
	var dd: float = row * pitch + C.PERSON_D
	var y: float = C.BASE_Y + (row + 1) * rise
	var zs := -1.0 if oval.ball.global_position.z < 0.0 else 1.0
	var seat := Vector3(oval.ball.global_position.x * 0.0, y, zs * (O.HALF_WID + O.FENCE + dd))
	var inward := Vector3(0, 0, -zs)
	# Empty the seats between the camera and him, and his neighbours, so nothing of today's crowd
	# stands in the foreground but him.
	_clear_seat(oval, seat, _env("CLEAR", 2.6))
	var fig := _load_figure(fig_path)
	oval.add_child(fig)
	var aabb := _aabb(fig)
	var k := height / maxf(0.01, aabb.size.y)
	fig.scale = Vector3.ONE * k
	fig.global_position = seat - Vector3(0, aabb.position.y * k, 0)
	fig.look_at(fig.global_position - inward, Vector3.UP)   # -Z away from the ground: the body's +Z faces in
	# Mixamo's materials import glossy (wet-looking cloth and skin): matte them.
	for m in fig.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = (m as MeshInstance3D).mesh
		for si in mesh.get_surface_count():
			var mat := mesh.surface_get_material(si)
			if mat is BaseMaterial3D:
				# Mixamo's roughness map multiplies the value down to wet shine: drop it.
				mat.roughness_texture = null
				mat.roughness = 0.9
				mat.metallic = 0.0
				mat.metallic_texture = null
				mat.metallic_specular = 0.2
				# Hair cards: cut out by their alpha and drawn from both sides.
				var tex: Texture2D = mat.albedo_texture
				if tex != null and tex.get_image() != null and tex.get_image().detect_alpha() != Image.ALPHA_NONE:
					mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_HASH
					mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	var ap := _anim_player(fig)
	if ap != null and ap.has_animation(clip):
		ap.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
		ap.play(clip)
	print("CLOSEUP figure %s: %.2f m tall unscaled, scale %.3f, clip %s (%s)" % [fig_path, aabb.size.y, k,
			clip, "playing" if ap != null and ap.has_animation(clip) else "MISSING"])
	var right := inward.cross(Vector3.UP)
	var cam: Camera3D = oval.camera
	cam.fov = _env("FOV", 50.0)
	cam.near = 0.05
	var eye := seat - inward * _env("BACK", 1.25) + right * _env("SIDE", 0.45) + Vector3(0, _env("EYE", 1.62), 0)
	cam.global_position = eye
	var tgt := eye + inward.rotated(Vector3.UP, deg_to_rad(_env("TURN", 0.0))) * 60.0
	tgt.y = 0.0
	cam.look_at(tgt, Vector3.UP)
	for i in range(frames):
		d.advance(DT)
		oval.sync(DT)
		# sync aims the camera at the play: put ours back.
		cam.global_position = eye
		cam.look_at(tgt, Vector3.UP)
		await process_frame
		await _save(oval, out, "f_%04d" % i)
	quit()


func _env(n: String, dflt: float) -> float:
	var v := OS.get_environment(n)
	return float(v) if v != "" else dflt


func _load_figure(p: String) -> Node3D:
	if p.begins_with("res://"):
		return (load(p) as PackedScene).instantiate()
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	var err := doc.append_from_file(p, st)
	assert(err == OK, "could not read " + p)
	return doc.generate_scene(st)


func _anim_player(n: Node) -> AnimationPlayer:
	if n is AnimationPlayer:
		return n
	for c in n.get_children():
		var a := _anim_player(c)
		if a != null:
			return a
	return null


func _aabb(n: Node3D) -> AABB:
	var box := AABB()
	var first := true
	for m in n.find_children("*", "MeshInstance3D", true, false):
		var mi := m as MeshInstance3D
		# Skinned: drawn by the skeleton's bones, so the mesh's own AABB is the body in metres
		# (Mixamo's Armature node carries a 0.01 scale its bones undo).
		var b := mi.get_aabb()
		box = b if first else box.merge(b)
		first = false
	return box


## Empty the crowd's seats round p (the candidate takes that seat).
func _clear_seat(oval, p: Vector3, r: float) -> void:
	for mmi in oval.crowd.find_children("*", "MultiMeshInstance3D", true, false):
		var mm: MultiMesh = mmi.multimesh
		for i in range(mm.instance_count):
			var t := mm.get_instance_transform(i)
			if Vector2(t.origin.x - p.x, t.origin.z - p.z).length() < r and absf(t.origin.y - p.y) < 2.0:
				mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * 0.0001), t.origin))
