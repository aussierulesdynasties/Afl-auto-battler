extends SceneTree
## Stills of one ground from cameras given in the MODEL's own metres (x east, y up, z south for a
## true-bearing model), for side-by-sides with Google Earth. Built as a match builds it.
##   godot --path . --rendering-method mobile --script tools/visual/ground_look.gd -- OUTDIR SLUG NAME:px,py,pz,tx,ty,tz[,fov] ...
## GROUND_LOOK_SIZE=WxH sets the frame (default 1280x720). Looks only.


func _initialize() -> void:
	_run.call_deferred()
	create_timer(1800.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	DirAccess.make_dir_recursive_absolute(out)
	var slug := str(args[1])
	var size := Vector2i(1280, 720)
	var sz := OS.get_environment("GROUND_LOOK_SIZE")
	if sz != "":
		var p := sz.split("x")
		size = Vector2i(int(p[0]), int(p[1]))
	root.size = size
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	OS.low_processor_usage_mode = false
	var g := ""
	for name in GroundModels.grounds():
		if GroundModels.slug_for(name) == slug:
			g = name
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new("SYD", gdb.club_list("SYD"), true, "SYD"),
			Squad_.new("COL", gdb.club_list("COL"), false, "COL"), 31).run()
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	oval.ground = g
	root.add_child(oval)
	oval.build(d, "SYD", "COL")
	oval.set_process(false)
	for c in oval.find_children("Crowd", "", true, false):
		c.visible = false
	var fit := GroundModels.fit_transform(slug)
	var cam: Camera3D = oval.camera
	cam.far = 4000.0
	cam.near = 0.1
	for i in 30:
		await process_frame
	for spec in args.slice(2):
		var parts := str(spec).split(":")
		var v := parts[1].split_floats(",")
		var pos: Vector3 = fit * Vector3(v[0], v[1], v[2])
		var tgt: Vector3 = fit * Vector3(v[3], v[4], v[5])
		cam.global_position = pos
		var up := Vector3.UP if absf((tgt - pos).normalized().y) < 0.99 else fit.basis * Vector3(0, 0, -1)
		cam.look_at(tgt, up)
		cam.fov = v[6] if v.size() > 6 else 60.0
		for i in 10:
			await process_frame
		root.get_viewport().get_texture().get_image().save_png(out.path_join("%s.png" % parts[0]))
		print("saved ", parts[0])
	quit(0)
