extends SceneTree
## Oval3DTurf.OPEN_UP, measured: for the day look and the late game, the exposure factor that keeps
## the open grass on the far wing (players hidden) at the brightness the look gives it at its own
## sun, for the sun at each of Oval3DTurf.OPEN_ALTS (a bisection, seven renders a height).
##   godot --path . --script tools/visual/measure_open_up3d.gd
## Prints one line a look; copy the factors into OPEN_UP.
const SIZE := Vector2i(640, 360)


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	var res: Dictionary = Sim.new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), 31).run()
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.size = SIZE
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	for p in oval.players:
		p["node"].visible = false
	var cam: Camera3D = oval.camera
	cam.global_position = oval.to_global(Vector3(10.0, 22.0, -25.0))
	cam.look_at(oval.to_global(Vector3(0.0, 0.0, -45.0)), Vector3.UP)
	var turf = oval.turf
	# By path, after the autoloads exist (Oval3DTurf reaches GameDB).
	var Turf = load("res://scripts/ui/match/Oval3DTurf.gd")
	turf.follow("", Oval3DSunClock.for_match("MCG", "Round 12", "day"))
	for slot in ["day", "twilight"]:
		var look: Dictionary = turf._looks[slot]
		var own: float = rad_to_deg(Turf._sun_height(look["sun"]))
		Turf.forced_open = 1.0
		turf._write(look, look, 0.0, own)
		var target := await _lum()
		var line := "%s own %.0f target %.1f:" % [slot, own, target]
		for alt in Turf.OPEN_ALTS:
			var lo := 0.3
			var hi := 4.0
			for i in range(7):
				var k := sqrt(lo * hi)
				Turf.forced_open = k
				turf._write(look, look, 0.0, alt)
				if await _lum() < target:
					lo = k
				else:
					hi = k
			line += " %.0f:%.2f" % [alt, sqrt(lo * hi)]
		print(line)
	Turf.forced_open = -1.0
	quit()


## The mean brightness (0 to 255) of the picture, on a grid.
func _lum() -> float:
	for i in range(3):
		await process_frame
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	var t := 0.0
	var n := 0
	for y in range(60, 300, 6):
		for x in range(60, 580, 6):
			t += img.get_pixel(x, y).get_luminance()
			n += 1
	return t / n * 255.0
