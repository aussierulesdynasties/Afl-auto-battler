extends SceneTree
## Every ground with a model in a match (row 202 2b, GroundModels): for each, the match's 3D oval
## built at that ground and filmed from a few fixed cameras, so one run checks that all of them
## load, sit on the turf and meet the boundary fence.
##   godot --path . --script tools/visual/capture_grounds3d.gd -- OUTDIR [W H] [GROUND ...]
## A GROUND is its name ("MCG") or its model folder ("mcg").
## Saves OUTDIR/<slug>_<shot>.png; prints LOAD ms per ground. The nightly ground shots
## (.github/workflows/ground-shots.yml, tools/ground_shots.py) compare these against the night before.

const SHOTS := [
	["high", Vector3(60, 170, 150), Vector3(0, 0, 0), 50.0],
	["wing", Vector3(0, 30, 70), Vector3(0, 0, 0), 48.0],
	["end", Vector3(-82, 24, 0), Vector3(20, 0, 0), 48.0],
	["fence", Vector3(-70, 2, 20), Vector3(-87, 1.5, 20), 60.0],
]


func _initialize() -> void:
	_run.call_deferred()
	create_timer(3000.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	DirAccess.make_dir_recursive_absolute(out)
	var size := Vector2i(800, 450)
	var only := []
	if args.size() >= 3 and str(args[1]).is_valid_int():
		size = Vector2i(int(args[1]), int(args[2]))
		only = args.slice(3)
	else:
		only = args.slice(1)
	root.size = size
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	OS.low_processor_usage_mode = false
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), 31).run()
	var grounds: Array = GroundModels.grounds()
	if not only.is_empty():
		grounds = []
		for want in only:
			var name := str(want)
			for g in GroundModels.grounds():
				if GroundModels.GROUNDS[g] == name:
					name = str(g)
			grounds.append(name)
	for g in grounds:
		var d = load("res://scripts/ui/match/MatchDirector.gd").new()
		d.setup(res, res["events"])
		var oval = load("res://scripts/ui/match/Oval3D.gd").new()
		oval.ground = str(g)
		root.add_child(oval)
		var t0 := Time.get_ticks_msec()
		oval.build(d, "FRE", "STK")
		var slug := GroundModels.slug_for(str(g))
		print("GROUND %s (%s) LOAD ms %d" % [g, slug, Time.get_ticks_msec() - t0])
		oval.set_process(false)
		# A new sky's light map takes about 30 frames to fill; filmed sooner, the first shot is dark.
		for i in 30:
			await process_frame
		var cam: Camera3D = oval.camera
		for s in SHOTS:
			cam.global_position = s[1]
			cam.look_at(s[2], Vector3.UP)
			cam.fov = s[3]
			for i in 6:
				await process_frame
			root.get_viewport().get_texture().get_image().save_png(out.path_join("%s_%s.png" % [slug, s[0]]))
		oval.queue_free()
		await process_frame
		await process_frame
	quit(0)
