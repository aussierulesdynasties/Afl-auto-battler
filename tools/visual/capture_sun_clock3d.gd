extends SceneTree
## The match clock's light (Oval3DTurf.follow, plan 2a.4): Sky3D's real sun over the ground as a
## match goes on, from the wing camera in a 16:9 TV picture.
##   godot --path . --script tools/visual/capture_sun_clock3d.gd -- OUTDIR [AT]
## A seeded Fremantle v St Kilda match played to AT seconds (default 14), then the same moment at
## each point of three matches' clocks: a winter twilight game at the MCG (bounce to the final
## siren, the sun setting in the first quarter), a winter day game there (the low sun of the last
## quarter) and a March night game (the bounce at dusk). Each frame's name carries the local time
## and the sun's height. The approved looks themselves (apply) are saved beside them to compare.

const SIZE := Vector2i(1280, 720)
const DT := 1.0 / 24.0
const MATCHES := [
	["MCG", "Round 12", "twilight", [[1, 0.0], [1, 15.0], [1, 25.0], [1, 30.0], [2, 40.0], [3, 75.0], [4, 120.0]]],
	["MCG", "Round 12", "day", [[1, 0.0], [3, 60.0], [4, 105.0], [4, 120.0]]],
	["MCG", "Opening Round", "night", [[1, 0.0], [1, 15.0], [1, 30.0], [2, 50.0]]],
]


func _initialize() -> void:
	_run.call_deferred()
	create_timer(900.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0]) if args.size() > 0 else "user://sun_clock3d"
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
	while played < at:
		d.advance(DT)
		oval.sync(DT)
		played += DT
		await process_frame
	for slot in ["day", "twilight", "night"]:
		oval.turf.clock = null
		oval.turf.apply("", slot)
		await _settle()
		await _save(out, "approved_%s" % slot)
	for m in MATCHES:
		var clock := Oval3DSunClock.for_match(m[0], m[1], m[2])
		oval.turf.follow("", clock)
		# A new sky's light map takes a few frames to fill the first time it is drawn.
		for i in range(30):
			await process_frame
		for qm in m[3]:
			var h := clock.hour_at(qm[0], qm[1])
			oval.turf.set_hour(h)
			await _settle()
			var name := "%s_%s_q%d_%02d%02d_sun%+.0f" % [m[2], str(m[1]).replace(" ", "").to_lower(), qm[0],
					int(h), int(fposmod(h, 1.0) * 60.0), clock.sun_altitude(h)]
			print(name)
			await _save(out, name)
	quit()


## A few frames so the sky's light map and the shadows catch up with the new light.
func _settle() -> void:
	for i in range(4):
		await process_frame


## Two pictures a moment: the wing camera on the play, and a low camera on the wing looking
## across to the far stand and the sky over it.
func _save(out: String, name: String) -> void:
	var oval = root.get_child(root.get_child_count() - 1)
	oval.aim_wing(18.0, 36.0)
	await _shot(out, name + "_play")
	var cam: Camera3D = oval.camera
	cam.global_position = oval.to_global(Vector3(0.0, 4.0, 72.0))
	cam.look_at(oval.to_global(Vector3(0.0, 30.0, -60.0)), Vector3.UP)
	await _settle()
	await _shot(out, name + "_sky")


func _shot(out: String, name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(out.path_join(name + ".png"))
