extends SceneTree
## A close look at one spot of a ground, built as a match builds it, for a fault the
## pre-inspection measured (preinspect_grounds.gd).
##   godot --path . --rendering-method mobile --script tools/visual/preinspect_look.gd -- OUTDIR GROUND NAME:px,py,pz,tx,ty,tz[,fov] ...
## Positions are the match's metres. PREINSPECT_NO_CROWD=1 hides the crowd (the seats as the fly-through shows them); PREINSPECT_NO_HUD=1 hides the score panel; PREINSPECT_MARK_MAT=<material> paints that material magenta; PREINSPECT_UP=x,y,z sets the camera's up. Saves OUTDIR/<slug>_<NAME>.png. Looks only.
## PREINSPECT_NEAR=m clips as the broadcast cameras do (Oval3DBroadcast.NEAR, 20 m). PREINSPECT_ROOF=open|shut sets a ground's opening roof (GroundModels.ROOFS; a match shows it shut).
## PREINSPECT_MODEL_FRAME=1 reads positions in the model's own frame instead (x east, y north, z up, metres), the frame
## Google Earth views are worked out in (docs/MCG_STANDARD.md); PREINSPECT_SIZE=WxH sets the picture (default 960x540).
## PREINSPECT_SUN=az,el puts the sun where it was in the Google Earth imagery (compass bearing from the model's north
## and elevation, degrees, and optionally the sun's energy; needs PREINSPECT_MODEL_FRAME), so colours compare under the same light, with its shadows
## drawn out to 1500 m.


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
	var model_frame := OS.get_environment("PREINSPECT_MODEL_FRAME") != ""
	var ground := oval.find_child("Ground", true, false) as Node3D
	cam.far = maxf(cam.far, 3000.0)   # a ground with a backdrop sees further (GroundModels.backdrop_far)
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
		# Straight down: model frame keeps the model's north (+y) at the top of the picture, as Google Earth does;
		# PREINSPECT_UP=x,y,z sets the camera's up outright.
		var north := (ground.global_transform.basis * Vector3.FORWARD).normalized() if model_frame and ground != null else Vector3.FORWARD
		var up := Vector3.UP if absf((tgt - pos).normalized().y) < 0.999 else north
		if OS.get_environment("PREINSPECT_UP") != "":
			var u := OS.get_environment("PREINSPECT_UP").split_floats(",")
			up = Vector3(u[0], u[1], u[2])
		cam.look_at(tgt, up)
		cam.fov = v[6] if v.size() > 6 else 60.0
		for i in 8:
			_place_sun(oval, ground, model_frame)
			await process_frame
		root.get_viewport().get_texture().get_image().save_png(out.path_join("%s_%s.png" % [GroundModels.slug_for(g), parts[0]]))
	quit(0)


## PREINSPECT_SUN: the sun's light along the bearing and elevation given in the model frame (x east, y north, z up).
func _place_sun(oval: Node, ground: Node3D, model_frame: bool) -> void:
	var sv := OS.get_environment("PREINSPECT_SUN").split_floats(",")
	if sv.size() < 2 or not model_frame or ground == null:
		return
	var sun := oval.get("_sun") as DirectionalLight3D
	if sun == null:
		return
	var az := deg_to_rad(sv[0])
	var el := deg_to_rad(sv[1])
	var m := Vector3(sin(az) * cos(el), cos(az) * cos(el), sin(el))   # towards the sun, model frame
	var to_sun := (ground.global_transform.basis * Vector3(m.x, m.z, -m.y)).normalized()
	sun.global_basis = Basis.looking_at(-to_sun, Vector3.UP if absf(to_sun.y) < 0.999 else Vector3.FORWARD)
	# The match draws shadows only 160-320 m out; a Google Earth camera 360 m up would see none (the bowl lit, the
	# roof's shade on the field missing), so the comparison shots draw them as far as the camera sees.
	sun.directional_shadow_max_distance = maxf(sun.directional_shadow_max_distance, 1500.0)
	if sv.size() > 2:
		sun.light_energy = sv[2]
