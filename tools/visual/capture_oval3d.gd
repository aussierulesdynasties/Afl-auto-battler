extends SceneTree
## PROTOTYPE capture of the 3D oval (director, 2026-11-14: "True 3D oval"):
##   godot --path . --script tools/visual/capture_oval3d.gd -- OUTDIR
## A seeded Fremantle v St Kilda match played through MatchDirector, the 3D oval copying it.
## Per size (PC 1920x1080 wing camera, phone 390x844 behind the goals): stills at a few
## moments, and SEQ frames of play for a moving clip. Prints the frame time.

const SIZES := [[Vector2i(1920, 1080), "wing"], [Vector2i(390, 844), "end"], [Vector2i(1920, 1080), "close"]]
const MOMENTS := [3.0, 14.0, 26.0]   # seconds of play
const SEQ := 72                      # frames at 1/24 s for the clip
const DT := 1.0 / 24.0


func _initialize() -> void:
	_run.call_deferred()
	create_timer(420.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0]) if args.size() > 0 else "user://oval3d"
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	var res: Dictionary = Sim.new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), 31).run()
	res["home"] = "FRE"
	res["away"] = "STK"
	res["label"] = "Round 1"
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	for entry in SIZES:
		var sz: Vector2i = entry[0]
		var cam: String = entry[1]
		root.size = sz
		DisplayServer.window_set_size(sz)
		var d = load("res://scripts/ui/match/MatchDirector.gd").new()
		d.setup(res, res["events"])
		var oval = load("res://scripts/ui/match/Oval3D.gd").new()
		root.add_child(oval)
		oval.build(d, "FRE", "STK")
		var tag := "%s_%dx%d" % [cam, sz.x, sz.y]
		var played := 0.0
		var spent := 0
		var frames := 0
		for m in MOMENTS:
			while played < m:
				d.advance(DT)
				oval.sync(DT)
				_aim(oval, cam)
				played += DT
				var t0 := Time.get_ticks_usec()
				await process_frame
				spent += Time.get_ticks_usec() - t0
				frames += 1
			await _save(out, "oval3d_%s_t%02d" % [tag, int(m)])
		DirAccess.make_dir_recursive_absolute(out.path_join("seq_" + tag))
		for i in range(SEQ):
			d.advance(DT)
			oval.sync(DT)
			_aim(oval, cam)
			await _save(out.path_join("seq_" + tag), "f%03d" % i)
		print("FRAME %s: %.2f ms a frame over %d frames, %d players" % [tag,
				float(spent) / maxf(1.0, frames) / 1000.0, frames, oval.players.size()])
		oval.queue_free()
		await process_frame
	quit()


func _aim(oval, cam: String) -> void:
	if cam == "wing":
		oval.aim_wing(30.0, 70.0)
	elif cam == "end":
		oval.aim_end(34.0, 52.0)
	else:
		oval.aim_close()


func _save(out: String, name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(out.path_join(name + ".png"))
