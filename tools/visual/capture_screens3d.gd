extends SceneTree
## The ground's big screens and fence signs in the 3D match (row 202 2b, Oval3DScreens): for each
## ground, the oval built for Fremantle v St Kilda, a score on the screens, then each screen filmed
## face on and from the main camera, the GOAL card, the replay on it, and the fence signs.
##   godot --path . --script tools/visual/capture_screens3d.gd -- OUTDIR [W H] [GROUND ...]
## Saves OUTDIR/<slug>_<shot>.png; prints SCREENS <ground> <count> per ground.


func _initialize() -> void:
	_run.call_deferred()
	create_timer(3000.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _snap(path: String) -> void:
	for i in 4:
		await process_frame
	root.get_viewport().get_texture().get_image().save_png(path)


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
	var grounds: Array = only if not only.is_empty() else GroundModels.grounds()
	for g in grounds:
		var d = load("res://scripts/ui/match/MatchDirector.gd").new()
		d.setup(res, res["events"])
		var oval = load("res://scripts/ui/match/Oval3D.gd").new()
		oval.ground = str(g)
		root.add_child(oval)
		oval.build(d, "FRE", "STK")
		oval.set_process(false)
		var slug := GroundModels.slug_for(str(g))
		if slug == "":
			slug = str(g).to_snake_case()
		var sc = oval.screens
		print("SCREENS %s %d" % [g, sc.faces.size()])
		sc.show_score([7, 9], [4, 11], "Q3 18'")
		var cam: Camera3D = oval.camera
		cam.fov = 40.0
		# The main camera's spot, looking at the end with the most screen.
		var k := 0
		for f in sc.faces:
			var mi := f as MeshInstance3D
			var at: Vector3 = mi.global_position
			var n: Vector3 = mi.global_transform.basis.z
			var w: float = (mi.mesh as QuadMesh).size.x
			cam.global_position = at + n * maxf(12.0, w * 1.6) + Vector3(0, 1.0, 0)
			cam.look_at(at, Vector3.UP)
			await _snap(out.path_join("%s_screen%d.png" % [slug, k]))
			if k == 0:
				sc.show_goal(1, "Max King", 12)
				await _snap(out.path_join("%s_goal.png" % slug))
				# The replay: the screens show what a camera behind the goals films.
				var tv := Camera3D.new()
				tv.top_level = true
				oval.add_child(tv)
				tv.global_position = Vector3(-at.x * 0.9, 12.0, 0.0)
				tv.look_at(Vector3(0, 0, 0), Vector3.UP)
				tv.fov = 35.0
				for i in 3:
					sc.frame(0.016, true, tv)
					await process_frame
				await _snap(out.path_join("%s_replay.png" % slug))
				sc.frame(0.016, false, tv)
				sc.frame(20.0, false, tv)
				tv.queue_free()
			k += 1
		# The fence signs: from the wing at fence height, and the main camera's view.
		cam.fov = 50.0
		cam.global_position = Vector3(20, 2.2, -40)
		cam.look_at(Vector3(-40, 0.6, -(MatchMotion.HALF_WID + 5.0)), Vector3.UP)
		await _snap(out.path_join("%s_signs.png" % slug))
		cam.global_position = Vector3(0, 30, 95)
		cam.look_at(Vector3(0, 0, 0), Vector3.UP)
		cam.fov = 48.0
		await _snap(out.path_join("%s_wing.png" % slug))
		oval.queue_free()
		await process_frame
		await process_frame
	quit(0)
