extends SceneTree
## Through the banner on the 3D ground (Oval3DBanner): every frame of the scene at 30 fps, for a
## clip (ffmpeg) and the QA stills, and the frame time of each shot.
##   godot --path . --rendering-method mobile --script tools/visual/capture_banner3d.gd -- OUTDIR [GROUND] [W H] [TEXT] [stills]
## With "stills" only the QA stills are drawn (a software renderer takes seconds a frame).
## GROUND defaults to the MCG; TEXT to a 200-game milestone (lines split on "|").
## Frames land in OUTDIR/f_0000.png...; stills of each shot as OUTDIR/still_<name>.png.

const FPS := 30.0


func _initialize() -> void:
	_run.call_deferred()
	create_timer(1500.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	DirAccess.make_dir_recursive_absolute(out)
	var ground := str(args[1]) if args.size() > 1 else "MCG"
	var size := Vector2i(1280, 720)
	if args.size() >= 4:
		size = Vector2i(int(args[2]), int(args[3]))
	var text := "200 games|Take a bow|Nat Fyfe"
	if args.size() >= 5:
		text = str(args[4])
	text = text.replace("|", "\n")
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
	oval.ground = ground
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	oval.turf.apply("", "day")
	oval.set_ends(1.0)
	oval.sync(0.0)
	var B = load("res://scripts/ui/match/Oval3DBanner.gd")
	var banner = B.new()
	oval.add_child(banner)
	banner.build(oval, 0, text, "FRE", 31)
	# The sky's light and the banner's face settle first.
	for i in 40:
		await process_frame
	var b0: float = banner._burst_at
	var stills := {int(0.6 * FPS): "wide", int((b0 - 0.3) * FPS): "front_hit", int((b0 + 0.35) * FPS): "front_burst",
			int((b0 + 1.2) * FPS): "front_after", int((b0 + 2.0) * FPS): "race", int((b0 + 3.6) * FPS): "race_end"}
	print("BURST at %.2f s, cuts %.2f %.2f, end %.2f" % [b0, banner.cut_front, banner.cut_back, banner.length])
	# The squad close up first (the QA check on their arms and hands), from the ground side.
	for spot in [[Vector3(-13.5, 1.6, 6.0), Vector3(-8.0, 1.5, -0.4), "squad_left"], [Vector3(-11.0, 1.8, -6.5), Vector3(-8.0, 1.5, -0.4), "squad_behind"]]:
		banner.frame(0.0)
		var cam: Camera3D = oval.camera
		cam.global_position = banner.global_transform * (spot[0] as Vector3)
		cam.look_at(banner.global_transform * (spot[1] as Vector3), Vector3.UP)
		cam.fov = 40.0
		await process_frame
		await RenderingServer.frame_post_draw
		root.get_viewport().get_texture().get_image().save_png(out.path_join("still_%s.png" % spot[2]))
	var only_stills := args.size() >= 6 and str(args[5]) == "stills"
	var n := 0
	var ms := {}
	while not banner.finished:
		var f0 := Time.get_ticks_usec()
		banner.frame(1.0 / FPS)
		if only_stills and not stills.has(n):
			n += 1
			continue
		await process_frame
		await RenderingServer.frame_post_draw
		var shot := "wide" if banner.t < banner.cut_front else ("front" if banner.t < banner.cut_back else "race")
		ms[shot] = ms.get(shot, []) + [(Time.get_ticks_usec() - f0) / 1000.0]
		var img := root.get_viewport().get_texture().get_image()
		if not only_stills:
			img.save_png(out.path_join("f_%04d.png" % n))
		if stills.has(n):
			img.save_png(out.path_join("still_%s.png" % stills[n]))
		n += 1
	for s in ms:
		var a: Array = ms[s]
		var sum := 0.0
		for v in a:
			sum += v
		print("SHOT %s frames %d mean ms %.1f" % [s, a.size(), sum / a.size()])
	print("FRAMES ", n)
	quit(0)
