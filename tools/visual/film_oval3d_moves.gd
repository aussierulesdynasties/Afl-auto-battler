extends SceneTree
## Film kicks, handballs and marks in a real match (row 198), close and side-on, for the
## self-check and for the director:
##   godot --path . --rendering-method mobile --script tools/visual/film_oval3d_moves.gd -- OUTDIR SEED W H WHO@T [WHO@T ...]
## Fremantle v St Kilda (seed 31 unless given) played at 60 frames a second, exactly as
## measure_oval3d_moves.gd plays it (so its "who=N t=T" lines name the moments). For each
## WHO@T, every frame from T-1.4 s to T+0.9 s is saved as <OUTDIR>/m<k>_<frame>.png, the camera
## 5 m to his side at chest height (FILM_CAM=broadcast: the match camera), following him (side-on as he turns). Moments
## must not overlap in time (one camera): film overlapping ones in separate runs. Every frame is a 60 Hz step: encoded at 60 fps
## it is game speed, at 30 fps half speed.

const DT := 1.0 / 60.0
const BEFORE_S := 1.4   # s filmed before each moment (FILM_BEFORE overrides: a chase-down's run)
const AFTER := 0.9


func _initialize() -> void:
	_run.call_deferred()
	create_timer(7000.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var a := OS.get_cmdline_user_args()
	var out := str(a[0])
	var seed := int(a[1])
	var size := Vector2i(int(a[2]), int(a[3]))
	var moments := []
	for k in range(4, a.size()):
		var parts := str(a[k]).split("@")
		moments.append({"who": int(parts[0]), "t": float(parts[1])})
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.size = size
	DisplayServer.window_set_size(size)
	var O = load("res://scripts/ui/match/Oval3D.gd")
	O.player_glb = "res://assets/oval3d/player_mh.glb"
	O.loops_glb = "res://assets/oval3d/player_mh.glb"
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), seed).run()
	res["home"] = "FRE"
	res["away"] = "STK"
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = O.new()
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	oval.turf.apply(str(res.get("weather", "")), "day")
	# Our own camera: the match's broadcast camera keeps moving itself between frames.
	# FILM_CAM=broadcast keeps the match's own camera (the picture as played) instead.
	var broadcast := OS.get_environment("FILM_CAM") == "broadcast"
	var cam := Camera3D.new()
	root.add_child(cam)
	cam.fov = 35.0
	cam.far = 2000.0
	var tv = null
	if broadcast:
		# The match's TV coverage (PitchView): the wing camera, set shots, ball-ups.
		oval.camera.make_current()
		tv = load("res://scripts/ui/match/Oval3DBroadcast.gd").new(oval)
	var BEFORE := float(OS.get_environment("FILM_BEFORE")) if OS.get_environment("FILM_BEFORE") != "" else BEFORE_S
	var t := 0.0
	var warm := false
	var frames := {}
	var side := {}
	var last_t := 0.0
	for m in moments:
		last_t = maxf(last_t, float(m["t"]))
	while not moments.is_empty() and t < last_t + AFTER + 0.1:
		d.advance(DT)
		oval.sync(DT)
		t += DT
		if tv != null:
			tv.frame(DT, t)
		if d.chasing_down() and not d.tackle_ahead().is_empty():
			print("FILM chase-down t=%.2f who=%d victim=%d" % [t, int(d.tackle_ahead()["who"]), int(d.tackle_ahead()["victim"])])
		for k in range(moments.size()):
			var m: Dictionary = moments[k]
			if t < float(m["t"]) - BEFORE or t > float(m["t"]) + AFTER:
				continue
			var node: Node3D = oval.players[int(m["who"])]["node"]
			# His hips, not his node: a move clip carries him metres off its origin.
			var sk: Skeleton3D = oval.players[int(m["who"])]["skel"]
			var at: Vector3 = sk.global_transform * sk.get_bone_global_pose(sk.find_bone("pelvis")).origin
			at.y = node.global_position.y
			# Side-on to the way he is facing, swung round smoothly as he turns (never a cut).
			var face := Vector3(sin(node.global_rotation.y), 0.0, cos(node.global_rotation.y))
			var want := face.cross(Vector3.UP).normalized()
			side[k] = want if not side.has(k) else (side[k] as Vector3).lerp(want, 0.08).normalized()
			cam.global_position = at + (side[k] as Vector3) * 5.0 + Vector3.UP * 1.3
			cam.look_at(at + Vector3.UP * 0.9, Vector3.UP)
			if not warm:
				for i in range(30):
					await process_frame
				warm = true
			if not broadcast:
				cam.make_current()
			await RenderingServer.frame_post_draw
			var f := int(frames.get(k, 0))
			root.get_viewport().get_texture().get_image().save_png(out.path_join("m%d_%04d.png" % [k, f]))
			frames[k] = f + 1
	print("FRAMES ", frames)
	quit(0)
