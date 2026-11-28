extends SceneTree
## A ground's model on the 3D oval (row 202 step 2b): stills from fixed cameras, for the
## director's check, and the time it takes to load and draw.
##   godot --path . --script tools/visual/capture_ground3d.gd -- OUTDIR GROUND [W H]
## Each shot: [name, eye, look-at, fov]; metres, x up the ground, y up, z across.
## Prints LOAD ms (build with the model) and, per shot, the mean frame time over 60 frames.

const SHOTS := [
	["wing", Vector3(0, 30, 70), Vector3(0, 0, 0), 48.0],
	["end", Vector3(-82, 24, 0), Vector3(20, 0, 0), 48.0],
	["high", Vector3(60, 170, 150), Vector3(0, 0, 0), 50.0],
	["seats", Vector3(30, 6, 40), Vector3(45, 6, 80), 50.0],
	["fence", Vector3(-70, 2, 20), Vector3(-87, 1.5, 20), 60.0],
]


func _initialize() -> void:
	_run.call_deferred()
	create_timer(900.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	DirAccess.make_dir_recursive_absolute(out)
	var size := Vector2i(1600, 900)
	if args.size() >= 4:
		size = Vector2i(int(args[2]), int(args[3]))
	root.size = size
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	OS.low_processor_usage_mode = false
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), 31).run()
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	oval.ground = str(args[1])
	root.add_child(oval)
	var t0 := Time.get_ticks_msec()
	oval.build(d, "FRE", "STK")
	print("LOAD ms ", Time.get_ticks_msec() - t0)
	oval.set_process(false)
	var cam: Camera3D = oval.camera
	for s in SHOTS:
		cam.global_position = s[1]
		cam.look_at(s[2], Vector3.UP)
		cam.fov = s[3]
		for i in 8:
			await process_frame
		var f0 := Time.get_ticks_usec()
		for i in 60:
			await process_frame
		print("SHOT %s frame ms %.2f" % [s[0], (Time.get_ticks_usec() - f0) / 60000.0])
		root.get_viewport().get_texture().get_image().save_png(out.path_join(str(s[0]) + ".png"))
	quit(0)
