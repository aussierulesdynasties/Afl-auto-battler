extends SceneTree
## Film a two-man clip (a speccy's jumper and his stepladder, keyed by key_pair.gd) on the match's
## own players: each man built and dressed as the match builds him (Oval3D._player and _dress: his
## club's guernsey, number, head, hair), on the match ground in its fine-day light, with the match ball.
##   godot --path . --rendering-method mobile --script tools/oval3d/film_pair.gd -- OUT_DIR A.res B.res A_PID B_PID YAW_DEG [DIST] [CATCH_S] [W H]
## A_PID, B_PID: GameDB player ids (e.g. MEL_11); each wears his own club's home guernsey. The pair
## plays at a spot on the ground away from the centre square's lines. YAW 0 looks along -z (the
## keyed spec's camera). CATCH_S: the ball flies in over the 0.5 s before (from FLIGHT_FROM) and then sits between the
## first man's palms (60% along each hand bone, as the match holds one). Writes OUT_DIR/f_<n>.png at
## 25 frames a second. Both men keep the body's standard build, so the keyed contact holds.

const GLB := "res://assets/oval3d/player_mh.glb"
const HZ := 25.0
const SPOT := Vector3(18.0, 0.0, 6.0)
const FLIGHT_S := 0.5


func _initialize() -> void:
	_run.call_deferred()
	create_timer(3000.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _palms(sk: Skeleton3D) -> Array:
	var pa: Array = []
	for side in ["l", "r"]:
		var hbn := sk.find_bone("hand_" + side)
		var g := sk.global_transform * sk.get_bone_global_pose(hbn)
		var hl := 0.0
		for c in sk.get_bone_children(hbn):
			hl += sk.get_bone_rest(c).origin.length()
		hl /= maxf(1.0, sk.get_bone_children(hbn).size())
		pa.append(g.origin + (sk.global_transform.basis * g.basis.y).normalized() * hl * 0.6)
	return pa


func _bone(sk: Skeleton3D, b: String) -> Vector3:
	return sk.global_transform * sk.get_bone_global_pose(sk.find_bone(b)).origin


func _run() -> void:
	await process_frame
	var a := OS.get_cmdline_user_args()
	var out := str(a[0])
	var pids := [str(a[3]), str(a[4])]
	var yaw := float(a[5])
	var dist := float(a[6]) if a.size() > 6 else 7.0
	var catch_s := float(a[7]) if a.size() > 7 else INF
	var size := Vector2i(int(a[8]), int(a[9])) if a.size() > 9 else Vector2i(960, 720)
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.use_debanding = true
	root.size = size
	DisplayServer.window_set_size(size)
	var O3 = load("res://scripts/ui/match/Oval3D.gd")
	O3.player_glb = GLB
	O3.loops_glb = GLB
	var gdb = root.get_node("GameDB")
	var clubs := [pids[0].split("_")[0], pids[1].split("_")[0]]
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new(clubs[0], gdb.club_list(clubs[0]), true, clubs[0]),
			Squad_.new(clubs[1], gdb.club_list(clubs[1]), false, clubs[1]), 31).run()
	res["home"] = clubs[0]
	res["away"] = clubs[1]
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = O3.new()
	root.add_child(oval)
	oval.build(d, clubs[0], clubs[1])
	oval.turf.apply("perfect", "day")
	for p in oval.players + oval.umpires:
		(p["node"] as Node3D).visible = false
	var scene: PackedScene = load(GLB)
	var men := []
	for i in 2:
		var who = gdb.player_by_id(pids[i])
		var p: Dictionary = oval._player(scene, oval._kit(gdb.club_guernsey(clubs[i])), gdb.club_colours(clubs[i]))
		oval._dress(p, {"pid": pids[i], "num": int((who as Dictionary).get("num", -1)) if who is Dictionary else -1})
		Oval3DBuild.apply(p, GLB, {}, "")
		(p["ring"] as Node3D).visible = false
		var n: Node3D = p["node"]
		n.global_position = SPOT
		n.rotation = Vector3.ZERO
		var ap: AnimationPlayer = p["anim"]
		var lib := AnimationLibrary.new()
		lib.add_animation("clip", load(str(a[1 + i])))
		ap.add_animation_library("pair", lib)
		ap.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
		ap.play("pair/clip")
		men.append(p)
		print("MAN %s %s" % [pids[i], (who as Dictionary).get("last", "?") if who is Dictionary else "?"])
	var ball: Node3D = oval.ball
	var bscale: Vector3 = ball.scale
	var cam: Camera3D = oval.camera
	cam.fov = 34.0
	cam.make_current()
	var ska: Skeleton3D = men[0]["skel"]
	var skb: Skeleton3D = men[1]["skel"]
	var length: float = (men[0]["anim"] as AnimationPlayer).current_animation_length
	var dir := Vector3(sin(deg_to_rad(yaw)), 0.0, cos(deg_to_rad(yaw)))
	# AIM_Y: the height the camera looks at (default 1.3 m; a speccy at the top wants about 1.6).
	var aim_y := float(OS.get_environment("AIM_Y")) if OS.get_environment("AIM_Y") != "" else 1.3
	# Where the ball is caught: the first man's palms at CATCH_S (flown in from up and in front of him).
	var catch_at := Vector3.INF
	# FLIGHT_FROM="x,z": the ground direction the ball comes from (default -z: in front of a man facing -z).
	var ff := OS.get_environment("FLIGHT_FROM").split(",") if OS.get_environment("FLIGHT_FROM") != "" else PackedStringArray(["0", "-1"])
	var flight_from := Vector3(float(ff[0]), 0.0, float(ff[1])).normalized()
	var t := 0.0
	var n := 0
	var warm := false
	while t <= length + 1e-4:
		for p in men:
			(p["anim"] as AnimationPlayer).seek(t, true)
		if catch_at == Vector3.INF and catch_s < INF:
			for p in men:
				(p["anim"] as AnimationPlayer).seek(catch_s, true)
			var pc: Array = _palms(ska)
			catch_at = (pc[0] + pc[1]) * 0.5
			for p in men:
				(p["anim"] as AnimationPlayer).seek(t, true)
		var mid := (_bone(ska, "pelvis") + _bone(skb, "pelvis")) * 0.5
		var aim := Vector3(mid.x, aim_y, mid.z)
		ball.visible = false
		if t >= catch_s - 1e-4:
			var pa: Array = _palms(ska)
			var across: Vector3 = (pa[0] - pa[1]).normalized()
			var fore: Vector3 = ((pa[0] + pa[1]) * 0.5 - _bone(ska, "lowerarm_l")).normalized()
			var long := across.cross(fore).cross(across).normalized()
			ball.global_transform = Transform3D(Basis(across, long.cross(across).normalized(), long), (pa[0] + pa[1]) * 0.5)
			ball.scale = bscale
			ball.visible = true
		elif t >= catch_s - FLIGHT_S:
			# Coming in on a dropping arc from in front of him (his facing at the catch) and above.
			var u := (t - (catch_s - FLIGHT_S)) / FLIGHT_S
			var from := catch_at + Vector3(0.0, 2.2, 0.0) + flight_from * 9.0
			var p := from.lerp(catch_at, u) + Vector3.UP * (1.0 - u) * u * 2.0
			ball.global_transform = Transform3D(Basis(Vector3.RIGHT, deg_to_rad(t * 600.0)), p)
			ball.scale = bscale
			ball.visible = true
		cam.global_position = aim + dir * dist
		cam.look_at(aim, Vector3.UP)
		if not warm:
			for i in 30:
				await process_frame
			warm = true
		await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("%s/f_%04d.png" % [out, n])
		n += 1
		t += 1.0 / HZ
	print("FILMED %d frames" % n)
	quit()
