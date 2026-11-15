extends SceneTree
## The 3D oval's turf under each weather and time of day (Oval3DTurf, row 197):
##   godot --path . --script tools/visual/capture_turf3d.gd -- OUTDIR [AT]
## A seeded Fremantle v St Kilda match played to AT seconds (default 14) on the 3D oval, then the
## same moment saved under every look, from the phone's behind-the-goals camera and the wing
## camera (PitchView's CAM3D_UP and CAM3D_BACK), and the close camera. Prints the frame time.

const SIZE := Vector2i(540, 1200)
const LOOKS := [["perfect", "day"], ["perfect", "twilight"], ["perfect", "night"],
		["wet", "day"], ["wet", "night"], ["hot", "day"], ["windy", "day"]]
const DT := 1.0 / 24.0
const UP := 18.0
const BACK := 28.0


func _initialize() -> void:
	_run.call_deferred()
	create_timer(600.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0]) if args.size() > 0 else "user://turf3d"
	var at := float(args[1]) if args.size() > 1 else 14.0
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
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	var played := 0.0
	var spent := 0
	var frames := 0
	while played < at:
		d.advance(DT)
		oval.sync(DT)
		oval.aim_end(UP, BACK)
		played += DT
		var t0 := Time.get_ticks_usec()
		await process_frame
		spent += Time.get_ticks_usec() - t0
		frames += 1
	print("FRAME: %.2f ms a frame over %d frames" % [float(spent) / maxf(1.0, frames) / 1000.0, frames])
	for look in LOOKS:
		oval.turf.apply(look[0], look[1])
		for cam in ["end", "wing", "close"]:
			if cam == "end":
				oval.aim_end(UP, BACK)
			elif cam == "wing":
				oval.aim_wing(UP, BACK * 1.3)
			else:
				oval.aim_close()
			# Two frames so the shadows and the light settle on the new look.
			await process_frame
			await _save(out, "turf_%s_%s_%s" % [look[1], look[0], cam])
	quit()


func _save(out: String, name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(out.path_join(name + ".png"))
