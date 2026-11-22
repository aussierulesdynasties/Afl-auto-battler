extends SceneTree
## A close look at one spot of a ground, built as a match builds it, for a fault the
## pre-inspection measured (preinspect_grounds.gd).
##   godot --path . --rendering-method mobile --script tools/visual/preinspect_look.gd -- OUTDIR GROUND NAME:px,py,pz,tx,ty,tz[,fov] ...
## Positions are the match's metres. PREINSPECT_NO_CROWD=1 hides the crowd (the seats as the fly-through shows them); PREINSPECT_NO_HUD=1 hides the score panel; PREINSPECT_MARK_MAT=<material> paints that material magenta; PREINSPECT_UP=x,y,z sets the camera's up. Saves OUTDIR/<slug>_<NAME>.png. Looks only.


func _initialize() -> void:
	_run.call_deferred()
	create_timer(1800.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	DirAccess.make_dir_recursive_absolute(out)
	var g := str(args[1])
	root.size = Vector2i(960, 540)
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	OS.low_processor_usage_mode = false
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), 31).run()
	for name in GroundModels.grounds():
		if GroundModels.slug_for(name) == g:
			g = name
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	oval.ground = g
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	oval.set_process(false)
	if OS.get_environment("PREINSPECT_NO_CROWD") != "":
		for c in oval.find_children("Crowd", "", true, false):
			c.visible = false
	# PREINSPECT_NO_HUD=1 hides the score panel and the other overlays (a ground check, not a broadcast).
	if OS.get_environment("PREINSPECT_NO_HUD") != "":
		for c in oval.find_children("*", "CanvasItem", true, false):
			(c as CanvasItem).visible = false
		for c in oval.find_children("*", "CanvasLayer", true, false):
			(c as CanvasLayer).visible = false
	# PREINSPECT_MARK_MAT=name draws that material's surfaces flat magenta (to find what a fault in a capture is).
	var mark := OS.get_environment("PREINSPECT_MARK_MAT")
	if mark != "":
		var flag := StandardMaterial3D.new()
		flag.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		flag.albedo_color = Color(1, 0, 1)
		for mi in oval.find_children("*", "MeshInstance3D", true, false):
			var m: Mesh = (mi as MeshInstance3D).mesh
			for i in (m.get_surface_count() if m else 0):
				var sm := m.surface_get_material(i)
				if sm and sm.resource_name == mark:
					(mi as MeshInstance3D).set_surface_override_material(i, flag)
	var cam: Camera3D = oval.camera
	cam.far = maxf(cam.far, 3000.0)   # a ground with a backdrop sees further (GroundModels.backdrop_far)
	cam.near = 0.05
	for spec in args.slice(2):
		var parts := str(spec).split(":")
		var v := parts[1].split_floats(",")
		cam.global_position = Vector3(v[0], v[1], v[2])
		# PREINSPECT_UP=x,y,z: the camera's up for a straight-down view (Vector3.UP is parallel to it there).
		var up := Vector3.UP
		if OS.get_environment("PREINSPECT_UP") != "":
			var u := OS.get_environment("PREINSPECT_UP").split_floats(",")
			up = Vector3(u[0], u[1], u[2])
		cam.look_at(Vector3(v[3], v[4], v[5]), up)
		cam.fov = v[6] if v.size() > 6 else 60.0
		for i in 8:
			await process_frame
		root.get_viewport().get_texture().get_image().save_png(out.path_join("%s_%s.png" % [GroundModels.slug_for(g), parts[0]]))
	quit(0)
