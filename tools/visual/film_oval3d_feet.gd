extends SceneTree
## Film one footballer's feet in a seeded match on the 3D oval (row 198, "no skating"):
##   godot --path . --rendering-method mobile --script tools/visual/film_oval3d_feet.gd -- OUTDIR T0 T1 [PLAYER] [W H] [SPEED]
## Fremantle v St Kilda, seed 31, on the MetaHuman body. From T0 to T1 seconds of play, a camera
## at knee height a few metres off him (fixed in its bearing, so his turns show) frames PLAYER
## (or whoever is nearest the ball at T0) and saves feet_NNNN.png at 30 frames a second of
## picture, SPEED times the match clock (1 unless given). Prints the player it followed, so a
## second run (another build) can film the same man for a side-by-side.

const WALL := 1.0 / 30.0
const BACK := 6.5              # m from him
const HIGH := 0.9              # m: the camera's height
const FOLLOW := 4.0            # 1/s: how fast the camera keeps up


func _initialize() -> void:
	_run.call_deferred()
	create_timer(5000.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var a := OS.get_cmdline_user_args()
	var out := str(a[0])
	var t0 := float(a[1])
	var t1 := float(a[2])
	var who := int(a[3]) if a.size() > 3 else -1
	var size := Vector2i(int(a[4]), int(a[5])) if a.size() > 5 else Vector2i(640, 480)
	var speed := float(a[6]) if a.size() > 6 else 1.0
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
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), 31).run()
	res["home"] = "FRE"
	res["away"] = "STK"
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = O.new()
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	oval.turf.apply(str(res.get("weather", "")), "day")
	var cam: Camera3D = oval.camera
	cam.current = true
	cam.fov = 32.0
	var T := 0.0
	var frame := 0
	var warm := false
	var eye := Vector3.INF
	while T < t1:
		var step: float = WALL * speed
		d.advance(step)
		T += step
		oval.sync(step)
		if T < t0:
			continue
		if who < 0:
			var bp: Vector2 = d.ball["pos"]
			var best := INF
			for i in range(oval.players.size()):
				var q: Vector3 = (oval.players[i]["node"] as Node3D).position
				var dist := Vector2(q.x, q.z).distance_to(bp)
				if dist < best:
					best = dist
					who = i
			print("PLAYER ", who)
		var him: Vector3 = (oval.players[who]["node"] as Node3D).global_position
		var want := him + Vector3(0.0, HIGH, BACK)
		eye = want if eye == Vector3.INF else eye.lerp(want, 1.0 - exp(-WALL * FOLLOW))
		cam.global_position = eye
		cam.look_at(Vector3(him.x, 0.75, him.z))
		if not warm:
			for i in range(30):
				await process_frame
			warm = true
		await RenderingServer.frame_post_draw
		root.get_viewport().get_texture().get_image().save_png(out.path_join("feet_%04d.png" % frame))
		frame += 1
	print("FRAMES ", frame)
	quit(0)
