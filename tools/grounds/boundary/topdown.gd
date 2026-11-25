extends SceneTree
## A traced ground as a match builds it (Oval3D), filmed straight down with an orthographic camera, so the
## match's painted boundary line can be measured against the Google Earth trace (tools/grounds/boundary/
## check_topdown.py), and seen against the model's own stands and fence.
##   godot --path . --rendering-method mobile --script tools/grounds/boundary/topdown.gd -- OUTDIR GROUND [PX] [METRES]
## Saves OUTDIR/<slug>_topdown.png (PX square, METRES across, default 2048 px over 220 m) and
## OUTDIR/<slug>_topdown.json: the camera ({metres, px}, match frame: image x = match x, image down = match +y)
## and the field the match played on (goal_x, the boundary sampled every degree).
## Looks only: nothing here changes a match.


func _initialize() -> void:
	_run.call_deferred()
	create_timer(1800.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	var g := str(args[1])
	var px := int(args[2]) if args.size() > 2 else 2048
	var metres := float(args[3]) if args.size() > 3 else 220.0
	root.size = Vector2i(px, px)
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), 31).run()
	res["venue"] = g
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	oval.ground = g
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	oval.set_process(false)
	# Nobody on the ground: only the turf, its paint and the model.
	for p in oval.players:
		((p as Dictionary)["node"] as Node3D).visible = false
	for u in oval.umpires:
		((u as Dictionary)["node"] as Node3D).visible = false
	if oval.ball != null:
		oval.ball.visible = false
	var cam: Camera3D = oval.camera
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.keep_aspect = Camera3D.KEEP_WIDTH
	cam.size = metres
	cam.near = 1.0
	cam.far = 1000.0
	# Straight down, match +x to the right of the picture and match +y (the 3D +z) down it.
	cam.global_transform = Transform3D(Basis(Vector3.RIGHT, -PI / 2.0), Vector3(0.0, 400.0, 0.0))
	for i in 10:
		await process_frame
	var slug := GroundModels.slug_for(g)
	DirAccess.make_dir_recursive_absolute(out)
	root.get_viewport().get_texture().get_image().save_png(out.path_join("%s_topdown.png" % slug))
	var ring := []
	for i in 360:
		var e := MatchMotion.edge_point(TAU * i / 360.0)
		ring.append([e.x, e.y])
	var f := FileAccess.open(out.path_join("%s_topdown.json" % slug), FileAccess.WRITE)
	f.store_string(JSON.stringify({"ground": g, "slug": slug, "px": px, "metres": metres, "shaped": MatchMotion.shaped(),
			"goal_x": MatchMotion.GOAL_X, "boundary": ring}))
	f.close()
	print("TOPDOWN %s shaped=%s goal_x=%.2f" % [slug, MatchMotion.shaped(), MatchMotion.GOAL_X])
	quit(0)
