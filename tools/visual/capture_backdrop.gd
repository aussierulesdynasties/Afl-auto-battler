extends SceneTree
## A ground's surroundings (GroundModels.backdrop, row 202 2b) from the broadcast cameras and from
## outside, built as a match builds it, with the triangles and draw calls each shot draws.
##   godot --path . --rendering-method mobile --script tools/visual/capture_backdrop.gd -- OUTDIR GROUND [slot] [nobackdrop]
## slot: day (default), twilight or night. nobackdrop hides the surroundings (the before picture).
## The picture is the phone's (1080 x 1240); wide makes it 1280 x 720; quick takes three of the shots.
## Saves OUTDIR/<slug>_<shot>.png and prints one "SHOT name tris draws" line per shot. Looks only.

const L := 86.3   # MatchMotion.HALF_LEN
const W := 67.4   # MatchMotion.HALF_WID


func _initialize() -> void:
	_run.call_deferred()
	create_timer(1800.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


## [name, eye, aim, width across the picture at the aim (m) or a field of view (degrees, < 0)].
func _shots() -> Array:
	var b = load("res://scripts/ui/match/Oval3DBroadcast.gd")
	var eye: Vector3 = b.main_eye()
	var up: float = b.EYE_UP
	var back: float = b.EYE_BACK
	var w50: float = b.wing_50()
	return [
		["main_far_wing", eye, Vector3(0, 1, -W), 57.0],
		["main_wide", eye, Vector3(0, 1, -W * 0.3), 150.0],
		["main_left_pocket", eye, Vector3(-L + 10, 1, -W * 0.6), 57.0],
		["main_right_pocket", eye, Vector3(L - 10, 1, -W * 0.6), 57.0],
		["wing50_left", eye + Vector3(-w50, 0, 0), Vector3(-L, 1, -20), 60.0],
		["wing50_right", eye + Vector3(w50, 0, 0), Vector3(L, 1, -20), 60.0],
		["goals_left", Vector3(L + back, up, 0), Vector3(-L, 3.3, 0), 42.0],
		["goals_right", Vector3(-(L + back), up, 0), Vector3(L, 3.3, 0), 42.0],
		["outside_city", Vector3(260, 90, 420), Vector3(-200, 30, -400), -55.0],
		["outside_park", Vector3(-420, 140, 380), Vector3(0, 0, 0), -50.0],
		["outside_high", Vector3(0, 650, 900), Vector3(0, 0, 0), -50.0],
	]


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	DirAccess.make_dir_recursive_absolute(out)
	var g := str(args[1])
	var slot := str(args[2]) if args.size() > 2 and str(args[2]) in ["day", "twilight", "night"] else "day"
	var hide := "nobackdrop" in args
	# The phone's match picture (portrait, rule: mobile first); "wide" for a 16:9 check.
	root.size = Vector2i(1280, 720) if "wide" in args else Vector2i(1080, 1240)
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	OS.low_processor_usage_mode = false
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new("COL", gdb.club_list("COL"), true, "COL"),
			Squad_.new("CAR", gdb.club_list("CAR"), false, "CAR"), 31).run()
	for name in GroundModels.grounds():
		if GroundModels.slug_for(name) == g:
			g = name
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	oval.ground = g
	root.add_child(oval)
	oval.build(d, "COL", "CAR")
	oval.set_process(false)
	if oval.turf != null and oval.turf.has_method("apply"):
		oval.turf.apply("", slot)
	if hide:
		for b in oval.find_children("Backdrop", "", true, false):
			b.visible = false
	var cam: Camera3D = oval.camera
	var quick := "quick" in args   # three shots: the broadcast wide shot and two from outside
	for s in _shots():
		if quick and not (s[0] in ["main_wide", "outside_park", "outside_high"]):
			continue
		# The broadcast cameras draw nothing nearer than 20 m (Oval3DBroadcast.NEAR, rule 2.101):
		# their mounts are in the stand.
		cam.near = 20.0 if float(s[3]) > 0.0 else 1.0
		cam.global_position = s[1]
		cam.look_at(s[2], Vector3.UP)
		var wdt: float = s[3]
		cam.fov = -wdt if wdt < 0.0 else rad_to_deg(2.0 * atan(wdt * 0.5 / (s[1] as Vector3).distance_to(s[2])))
		for i in 6:
			await process_frame
		var tris := RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)
		var draws := RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)
		print("SHOT %s %d %d" % [s[0], tris, draws])
		root.get_viewport().get_texture().get_image().save_png(out.path_join("%s_%s%s.png" % [GroundModels.slug_for(g), s[0], "_before" if hide else ""]))
	print("VRAM_MB %.0f" % (Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0))
	quit(0)
