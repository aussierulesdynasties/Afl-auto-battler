extends SceneTree
## The live oval on its own, for the director's eye and for the frame-time number:
##   godot --path . --script tools/visual/capture_live_oval.gd -- OUTDIR [--old res://path/PitchViewOld.gd]
## A seeded Fremantle v St Kilda match on a phone (390x844, the oval upright in the
## match screen's own band) and a PC (1920x1080), dark theme. Saves, per size:
##   oval_centre_bounce, oval_goal (the frame after the first goal), oval_bench_open
##   (the drawer open, one hurt and one tired player on the bench so their marks
##   show), oval_windy (flags on the roof), oval_day and oval_twilight.
## Then prints how long the oval's own drawing takes a frame (script time in _draw,
## 240 frames of play at each size). With --old (a copy of another branch's
## PitchView under another class name) the same match is timed on that one too, in
## the same process, so the two numbers compare. Looks only: it reads a match
## result and writes nothing but the pictures.

const SIZES := [Vector2i(390, 844), Vector2i(1920, 1080)]
const PHONE_BAND := Rect2(12, 135, 366, 472)   # where the match screen puts the oval on a 390x844 phone
const TIMED := "extends \"%s\"\nvar spent := 0\nvar frames := 0\nfunc _draw() -> void:\n\tvar t := Time.get_ticks_usec()\n\tsuper._draw()\n\tspent += Time.get_ticks_usec() - t\n\tframes += 1\n"


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0]) if args.size() > 0 else "user://"
	var old := ""
	for i in range(args.size() - 1):
		if str(args[i]) == "--old":
			old = str(args[i + 1])
	DirAccess.make_dir_recursive_absolute(out)
	# The game ships in low-processor mode: a still screen draws nothing, and a wait
	# for the next drawn frame would never end.
	OS.low_processor_usage_mode = false
	var UK = load("res://scripts/ui/UiKit.gd")
	UK.apply_appearance("dark")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	var Marks = load("res://scripts/ui/match/PlayerMarks.gd")
	var gdb = root.get_node("GameDB")
	var res: Dictionary = Sim.new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), 31).run()
	res["home"] = "FRE"
	res["away"] = "STK"
	res["weather"] = "perfect"
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	for sz in SIZES:
		root.size = sz
		DisplayServer.window_set_size(sz)
		for i in range(4):
			await process_frame
		var tag := "%dx%d" % [sz.x, sz.y]
		var phone: bool = sz.x < sz.y
		# The look, frame by frame.
		var pv = _view("res://scripts/ui/PitchView.gd", res, phone, sz)
		await _settle(pv, 30)
		await _save(out, "oval_centre_bounce_%s" % tag)
		pv.set_speed(4.0)
		pv.play()
		var goal := [false]
		pv.event_played.connect(func(ev):
			if str(ev.get("kind", "")) == "goal":
				goal[0] = true)
		var guard := 0
		while not goal[0] and guard < 6000:
			guard += 1
			await process_frame
		for i in range(6):
			await process_frame
		await _save(out, "oval_goal_%s" % tag)
		pv.playing = false
		var bench: Array = pv.director.bench
		if bench.size() == 2 and (bench[0] as Array).size() > 1:
			pv.set_marks({str(bench[0][1]["pid"]): {"mark": Marks.HURT, "words": "Injured: hamstring strain"},
					str(bench[1][3]["pid"]): {"mark": Marks.TIRED, "words": "Tired: running on empty"}})
		pv.open_bench()
		await _settle(pv, 6)
		await _save(out, "oval_bench_open_%s" % tag)
		pv.close_bench()
		pv.queue_free()
		await process_frame
		for look in [["windy", "", "oval_windy"], ["perfect", "day", "oval_day"], ["perfect", "twilight", "oval_twilight"]]:
			var r2 := res.duplicate()
			r2["weather"] = look[0]
			var pv2 = _view("res://scripts/ui/PitchView.gd", r2, phone, sz)
			if "time_override" in pv2:
				pv2.time_override = str(look[1])
			pv2.set_speed(4.0)
			pv2.play()
			for i in range(150):
				await process_frame
			await _save(out, "%s_%s" % [look[2], tag])
			pv2.queue_free()
			await process_frame
		# The frame-time number.
		for which in [["this branch", "res://scripts/ui/PitchView.gd"], ["the old oval", old]]:
			if str(which[1]) == "":
				continue
			for weather in ["perfect", "windy"]:
				var r3 := res.duplicate()
				r3["weather"] = weather
				var timed = _view(str(which[1]), r3, phone, sz, true)
				timed.set_speed(4.0)
				timed.play()
				for i in range(30):
					await process_frame
				timed.spent = 0
				timed.frames = 0
				for i in range(240):
					timed.queue_redraw()
					await process_frame
				print("OVAL DRAW %s, %s, %s: %.3f ms a frame (%d frames)" % [tag, weather, str(which[0]),
						float(timed.spent) / 1000.0 / float(maxi(1, timed.frames)), timed.frames])
				timed.queue_free()
				await process_frame
	quit(0)


func _view(path: String, res: Dictionary, phone: bool, sz: Vector2i, timed := false):
	var pv
	if timed:
		var sc := GDScript.new()
		sc.source_code = TIMED % path
		sc.reload()
		pv = sc.new()
	else:
		pv = load(path).new()
	root.add_child(pv)
	if phone:
		pv.position = PHONE_BAND.position
		pv.size = PHONE_BAND.size
		pv.upright = true
		pv.camera_enabled = false
	else:
		pv.position = Vector2.ZERO
		pv.size = Vector2(sz)
		pv.camera_enabled = false
	pv.setup(res)
	return pv


func _settle(pv, frames: int) -> void:
	for i in range(frames):
		pv.queue_redraw()
		await process_frame


func _save(out: String, name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	var path := out.path_join(name + ".png")
	print("saved ", path, " ", img.save_png(path))
