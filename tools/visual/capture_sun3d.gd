extends SceneTree
## The real sun over a ground (Oval3DSunClock.sun_basis, data/ground_places.json "axis"): the
## stadium seen from high on its north side and its south side, and the wing camera on the play,
## so the sunlit face can be checked against Google Earth and real photos (in Australia the sun is
## in the north: the north faces lit, the south ones in shade).
##   godot --path . --rendering-method mobile --script tools/visual/capture_sun3d.gd -- OUTDIR [GROUNDS] [SLOTS]
## GROUNDS ground names, comma-separated (default "Optus Stadium,MCG,Marvel Stadium"); SLOTS
## times of day (default "day,twilight"). Each frame: <ground slug>_<slot>_<view>.png, where view
## is north (looking south at the north face), south (looking north at the south face) or play.

const SIZE := Vector2i(1280, 720)
const DT := 1.0 / 24.0


func _initialize() -> void:
	_run.call_deferred()
	create_timer(1500.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0]) if args.size() > 0 else "user://sun3d"
	var grounds := (str(args[1]) if args.size() > 1 else "Optus Stadium,MCG,Marvel Stadium").split(",")
	var slots := (str(args[2]) if args.size() > 2 else "day,twilight").split(",")
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	var res: Dictionary = Sim.new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), 31).run()
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.size = SIZE
	DisplayServer.window_set_size(SIZE)
	for ground in grounds:
		var d = load("res://scripts/ui/match/MatchDirector.gd").new()
		d.setup(res, res["events"])
		var oval = load("res://scripts/ui/match/Oval3D.gd").new()
		oval.ground = ground
		oval.quality = "high"
		Oval3DQuality.apply_viewport("high", root.get_viewport())
		root.add_child(oval)
		oval.build(d, "FRE", "STK")
		var played := 0.0
		while played < 6.0:
			d.advance(DT)
			oval.sync(DT)
			played += DT
			await process_frame
		var slug := GroundModels.slug_for(ground)
		var axis := Oval3DSunClock.axis_for(ground)
		for slot in slots:
			oval.turf.apply("", slot)
			var c := Oval3DSunClock.for_match(ground, "", slot)
			var s := c.sun_at(c.kickoff)
			print("%s %s: axis %.1f, sun %.1f up at bearing %.1f (%02d:%02d)" % [ground, slot, axis, s.x, s.y,
					int(c.kickoff), int(fmod(c.kickoff, 1.0) * 60.0)])
			for i in range(30):
				await process_frame
			await _views(oval, out, "%s_%s" % [slug if slug != "" else ground.to_snake_case(), slot], axis)
		oval.queue_free()
		await process_frame
	quit()


## A horizontal direction in the ground's frame for a compass bearing.
static func toward(bearing: float, axis: float) -> Vector3:
	var phi := deg_to_rad(bearing - axis)
	return Vector3(cos(phi), 0.0, sin(phi))


func _views(oval, out: String, name: String, axis: float) -> void:
	var cam: Camera3D = oval.camera
	for v in [["north", 0.0], ["south", 180.0]]:
		var from: Vector3 = toward(v[1], axis) * 330.0 + Vector3(0.0, 150.0, 0.0)
		cam.global_position = oval.to_global(from)
		cam.look_at(oval.to_global(Vector3(0.0, 10.0, 0.0)), Vector3.UP)
		await _shot(out, "%s_%s" % [name, v[0]])
	oval.aim_wing(18.0, 36.0)
	await _shot(out, name + "_play")


func _shot(out: String, name: String) -> void:
	for i in range(4):
		await process_frame
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(out.path_join(name + ".png"))
	print("saved ", name)
