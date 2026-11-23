extends SceneTree
## A close look at one spot of a ground, built as a match builds it, for a fault the
## pre-inspection measured (preinspect_grounds.gd).
##   godot --path . --rendering-method mobile --script tools/visual/preinspect_look.gd -- OUTDIR GROUND NAME:px,py,pz,tx,ty,tz[,fov] ...
## Positions are the match's metres. PREINSPECT_NO_CROWD=1 hides the crowd (the seats as the fly-through shows them). Saves OUTDIR/<slug>_<NAME>.png. Looks only.
## PREINSPECT_NEAR=m clips as the broadcast cameras do (Oval3DBroadcast.NEAR, 20 m). PREINSPECT_ROOF=open|shut sets a ground's opening roof (GroundModels.ROOFS; a match shows it shut).
## PREINSPECT_MODEL_FRAME=1 reads positions in the model's own frame instead (x east, y north, z up, metres), the frame
## Google Earth views are worked out in (docs/MCG_STANDARD.md); PREINSPECT_SIZE=WxH sets the picture (default 960x540).
## PREINSPECT_SUN=bearing,elevation[,energy] puts the sun where it was when a reference photo was taken (degrees, model frame,
## bearing from north towards east), so a face lit in the photo is lit in the picture and colours compare like for like.


func _initialize() -> void:
	_run.call_deferred()
	create_timer(1800.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	DirAccess.make_dir_recursive_absolute(out)
	var g := str(args[1])
	var sz := OS.get_environment("PREINSPECT_SIZE").split("x")
	root.size = Vector2i(int(sz[0]), int(sz[1])) if sz.size() == 2 else Vector2i(960, 540)
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
	if OS.get_environment("PREINSPECT_ROOF") != "":
		var gr: Node = oval.find_child("Ground", true, false)
		if gr != null:
			GroundModels.set_roof(gr, GroundModels.slug_for(g), OS.get_environment("PREINSPECT_ROOF") == "shut")
	var cam: Camera3D = oval.camera
	var model_frame := OS.get_environment("PREINSPECT_MODEL_FRAME") != ""
	var ground := oval.find_child("Ground", true, false) as Node3D
	if OS.get_environment("PREINSPECT_SUN") != "" and ground != null:
		var sv := OS.get_environment("PREINSPECT_SUN").split_floats(",")
		var b := deg_to_rad(sv[0])
		var e := deg_to_rad(sv[1])
		var to_sun := Vector3(sin(b) * cos(e), cos(b) * cos(e), sin(e))    # model frame: x east, y north, z up
		var sun_d := (ground.global_basis * Vector3(to_sun.x, to_sun.z, -to_sun.y)).normalized()
		var sun: DirectionalLight3D = null
		for l: DirectionalLight3D in oval.find_children("*", "DirectionalLight3D", true, false):
			if l.visible and (sun == null or l.light_energy > sun.light_energy):
				sun = l
		if sun != null:
			sun.global_basis = Basis.looking_at(-sun_d, Vector3.UP)
			sun.directional_shadow_max_distance = 1500.0
			if sv.size() > 2:
				sun.light_energy = sv[2]
	cam.far = 3000.0
	cam.near = float(OS.get_environment("PREINSPECT_NEAR")) if OS.get_environment("PREINSPECT_NEAR") != "" else 0.05
	for spec in args.slice(2):
		var parts := str(spec).split(":")
		var v := parts[1].split_floats(",")
		var pos := Vector3(v[0], v[1], v[2])
		var tgt := Vector3(v[3], v[4], v[5])
		if model_frame and ground != null:
			pos = ground.global_transform * Vector3(pos.x, pos.z, -pos.y)
			tgt = ground.global_transform * Vector3(tgt.x, tgt.z, -tgt.y)
		cam.global_position = pos
		# Straight down: screen-up is true north in the model frame (the ground is turned in the game's world, so
		# the world's FORWARD put Marvel's top view 90 degrees round from Google Earth's, PC check 2026-11-23)
		var down_up := (ground.global_basis * Vector3(0.0, 0.0, -1.0)).normalized() if model_frame and ground != null else Vector3.FORWARD
		cam.look_at(tgt, Vector3.UP if absf((tgt - pos).normalized().y) < 0.999 else down_up)
		cam.fov = v[6] if v.size() > 6 else 60.0
		for i in 8:
			await process_frame
		root.get_viewport().get_texture().get_image().save_png(out.path_join("%s_%s.png" % [GroundModels.slug_for(g), parts[0]]))
	quit(0)
