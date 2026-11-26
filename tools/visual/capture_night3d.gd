extends SceneTree
## A night match at a real ground under its lights (Oval3DTowers, rule 2.82): the broadcast
## pictures a coach sees, to set against real night-match footage.
##   godot --path . --rendering-method mobile --script tools/visual/capture_night3d.gd -- OUTDIR [GROUND] [LEVELS] [SLOTS]
## GROUND a ground's name (default "MCG"); LEVELS graphics levels, comma-separated (default
## "high"); SLOTS times of day (default "night"). A seeded Fremantle v St Kilda match played 14 s,
## then per level and slot: the wing camera on the play, a close camera on the men (their
## shadows), a wide shot from the members' wing over the ground to the far towers, and a low
## shot across to the far stand and the sky. Each frame's name: <slot>_<level>_<view>.png.

const SIZE := Vector2i(1280, 720)
const DT := 1.0 / 24.0


func _initialize() -> void:
	_run.call_deferred()
	create_timer(900.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0]) if args.size() > 0 else "user://night3d"
	var ground := str(args[1]) if args.size() > 1 else "MCG"
	var levels := (str(args[2]) if args.size() > 2 else "high").split(",")
	var slots := (str(args[3]) if args.size() > 3 else "night").split(",")
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
	for level in levels:
		var d = load("res://scripts/ui/match/MatchDirector.gd").new()
		d.setup(res, res["events"])
		var oval = load("res://scripts/ui/match/Oval3D.gd").new()
		oval.ground = ground
		oval.quality = level
		Oval3DQuality.apply_viewport(level, root.get_viewport())
		root.add_child(oval)
		oval.build(d, "FRE", "STK")
		if oval.towers != null:
			print("towers: ", oval.towers.banks.size(), " banks ", oval.towers.banks)
		var played := 0.0
		while played < 14.0:
			d.advance(DT)
			oval.sync(DT)
			played += DT
			await process_frame
		for slot in slots:
			oval.turf.apply("", slot)
			if oval.towers != null:
				print("%s: level %.2f, roof lights %s, shadowed beams %d" % [slot, oval.towers.level,
						oval.towers._roofline.multimesh.instance_count if oval.towers._roofline else 0,
						oval.towers.beams.filter(func(b): return b.visible).size()])
			for i in range(30):
				await process_frame
			await _views(oval, out, "%s_%s" % [slot, level])
		oval.queue_free()
		await process_frame
	quit()


func _views(oval, out: String, name: String) -> void:
	var cam: Camera3D = oval.camera
	oval.aim_wing(18.0, 36.0)
	await _shot(out, name + "_play")
	# Close on the men: low and near, so each man's shadows show round his feet.
	var c := Vector3.ZERO
	for p in oval.players:
		c += (p["node"] as Node3D).position
	c /= maxf(1.0, oval.players.size())
	var near: Node3D = oval.players[0]["node"]
	var best := 1e9
	for p in oval.players:
		var n: Node3D = p["node"]
		if n.position.distance_to(c) < best:
			best = n.position.distance_to(c)
			near = n
	cam.global_position = oval.to_global(near.position + Vector3(6.0, 4.0, 9.0))
	cam.look_at(oval.to_global(near.position + Vector3(0, 0.6, 0)), Vector3.UP)
	await _shot(out, name + "_close")
	# Wide: high on the members' wing over the whole ground to the far towers and the sky.
	cam.global_position = oval.to_global(Vector3(-20.0, 32.0, 95.0))
	cam.look_at(oval.to_global(Vector3(0.0, 8.0, -20.0)), Vector3.UP)
	await _shot(out, name + "_wide")
	# Low on the wing across to the far stand and the sky.
	cam.global_position = oval.to_global(Vector3(0.0, 4.0, 72.0))
	cam.look_at(oval.to_global(Vector3(0.0, 30.0, -60.0)), Vector3.UP)
	await _shot(out, name + "_sky")


func _shot(out: String, name: String) -> void:
	for i in range(4):
		await process_frame
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(out.path_join(name + ".png"))
	print("saved ", name)
