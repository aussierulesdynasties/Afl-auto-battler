extends SceneTree
## The aerial orbit round a ground (Oval3DOrbit), built as a match builds it: stills round the circle
## for checking everything the orbit shows, or every frame of a lap for a film.
##   godot --path . --rendering-method mobile --script tools/visual/capture_orbit.gd -- OUTDIR GROUND [options]
## Options:
##   stills=N      N pictures evenly round the circle (default 24), saved OUTDIR/<slug>_orbit_<deg>.png
##   film=S        instead, S seconds of the orbit at fps frames a second, OUTDIR/<slug>_f<nnnnn>.png
##   from=DEG      the film starts this many degrees round (default 0)
##   fps=N         (default 30)
##   size=WxH      the picture (default 1280x720)
##   slot=day|twilight|night
##   nobackdrop    the far surroundings hidden after planning (which part of a picture is whose)
## Prints "ORBIT radius r_out top fov low high" and one "STILL deg eye" line per picture. Looks only.


func _initialize() -> void:
	_run.call_deferred()
	create_timer(7000.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _opt(args: Array, key: String, dflt: String) -> String:
	for a in args:
		if str(a).begins_with(key + "="):
			return str(a).substr(key.length() + 1)
	return dflt


func _run() -> void:
	await process_frame
	var args := Array(OS.get_cmdline_user_args())
	var out := str(args[0])
	DirAccess.make_dir_recursive_absolute(out)
	var g := str(args[1])
	var sz := _opt(args, "size", "1280x720").split("x")
	root.size = Vector2i(int(sz[0]), int(sz[1]))
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	OS.low_processor_usage_mode = false
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new("COL", gdb.club_list("COL"), true, "COL"),
			Squad_.new("CAR", gdb.club_list("CAR"), false, "CAR"), 31).run()
	for name in GroundModels.grounds():
		if GroundModels.slug_for(name) == g:
			g = name
	var slug := GroundModels.slug_for(g)
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	oval.ground = g
	root.add_child(oval)
	oval.build(d, "COL", "CAR")
	oval.set_process(false)
	var slot := _opt(args, "slot", "day")
	if oval.turf != null and oval.turf.has_method("apply"):
		oval.turf.apply("", slot)
	print("PARTS ", ", ".join(oval.get_node("Ground").get_children().map(func(c): return str(c.name))))
	var t0 := Time.get_ticks_msec()
	var orbit := Oval3DOrbit.plan(oval, GroundModels.match_fence(), slug)
	var lo := INF
	var hi := -INF
	for y in orbit.heights:
		lo = minf(lo, y)
		hi = maxf(hi, y)
	print("ORBIT %s radius %.0f r_out %.0f top %.0f fov %.1f low %.0f high %.0f (planned in %d ms)" % [slug,
			orbit.radius, orbit.r_out, orbit.top, orbit.fov, lo, hi, Time.get_ticks_msec() - t0])
	if "nobackdrop" in args:
		for b in oval.find_children("Backdrop", "", true, false):
			b.visible = false
	var cam: Camera3D = oval.camera
	cam.far = maxf(cam.far, orbit.radius + 8000.0)
	for i in 40:   # a new sky's light map takes ~30 frames
		await process_frame
	var film := float(_opt(args, "film", "0"))
	if film > 0.0:
		var fps := int(_opt(args, "fps", "30"))
		var t_from := float(_opt(args, "from", "0")) / 360.0 * Oval3DOrbit.LAP_S
		for f in int(film * fps):
			orbit.place(cam, t_from + float(f) / fps)
			await RenderingServer.frame_post_draw
			root.get_viewport().get_texture().get_image().save_png(out.path_join("%s_f%05d.png" % [slug, f]))
			if f % 100 == 0:
				print("FRAME %d" % f)
	else:
		var n := int(_opt(args, "stills", "24"))
		for k in n:
			var deg := 360.0 * k / n + float(_opt(args, "from", "0"))
			orbit.place(cam, deg / 360.0 * Oval3DOrbit.LAP_S)
			for i in 6:
				await process_frame
			print("STILL %03d %s" % [int(deg), str(cam.global_position.snapped(Vector3.ONE))])
			root.get_viewport().get_texture().get_image().save_png(out.path_join("%s_orbit_%03d.png" % [slug, int(deg)]))
	quit(0)
