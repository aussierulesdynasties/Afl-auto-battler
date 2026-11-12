extends SceneTree
## The set-shot call on the match screen: the scene and the call over it, one capture
## per spot MatchSim kicks from (MatchSim.SET_BANDS_ON), each fired through the real
## call (MatchSim._offer_set_shot), so the headline is the one a match shows. Needs a
## real renderer (windowed, through C:/kt/gpu_slot.sh on this machine):
##   godot --path . --script tools/visual/capture_set_shot.gd -- --out /tmp/ss [--size 390x844]
##       [--club COL] [--bands close,front,angle,pocket,long] [--venue MCG] [--topdown] [--clip]
## Writes <out>_<band>.png (frozen, the call up) and prints a MEASURE line per band: where
## the kicker and the man on the mark stand on the oval, metres to the middle of the goal
## line, the angle off the line through the goals, and whether the 50 m arc lies between
## the kicker and the goal. --topdown also writes <out>_topdown.png: the attacking end
## drawn to scale from above, every spot's kicker, mark and camera where the scene put them.
## ART lines name every figure move drawn (the sheet's own moves, not a fallback).
## --clip also writes every frame from the cut to the settled call, <out>_<band>_clip/NNN.png:
## run Godot with --fixed-fps 30 so the frames are 1/30 s apart, then stitch them.

var W := 390
var H := 844
var _out := "/tmp/ss"
var _MS: GDScript
var _VG: GDScript


func _initialize() -> void:
	# A script error stops _run without quitting: give up rather than hold the GPU.
	create_timer(300.0).timeout.connect(func() -> void:
		print("TIMED OUT")
		quit(1))
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(path: String) -> void:
	await _frames(2)
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png(path)
	print("wrote ", path, " ", img.get_size())


## A live match with the set-shot call up from the band's spot.
func _stage(club: String, key: String, venue: String) -> Control:
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.set_vignettes_on(true)
	state.reset()
	state.replay_seed = 2027
	state.start_season(club, db.club_list(club))
	state.prepare_interactive_match()
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	await _frames(8)
	(m.find_child("StartQuarter", true, false) as Button).emit_signal("pressed")
	await _frames(8)
	# The way a live call comes up: the oval has played everything the sim has rolled, so the
	# scoreboard and the big screen show the same score (MatchScene._on_finished, as Skip to
	# the break releases it).
	m.set("_skipping", true)
	m.get("_pitch").release_all()
	m.set("_skipping", false)
	if venue != "":
		_VG.venue = venue
	var sim = state.pending_sim
	var me := int(m.get("_my_side"))
	var mine: Array = sim.squads[me].ground
	var theirs: Array = sim.squads[1 - me].ground
	var shooter: Dictionary = mine.filter(func(p): return str(p["role"]) == "FWD")[0]
	var feeder: Dictionary = mine.filter(func(p): return str(p["role"]) == "MID")[0]
	var defender: Dictionary = theirs.filter(func(p): return str(p["role"]) == "DEF")[0]
	var band: Dictionary = {}
	for b in _MS.set_bands(0.34):
		if str(b["key"]) == key:
			band = b
	sim.pending_moment = {}
	sim.moment_side = me
	var goal_line := float((load("res://scripts/sim/Ratings.gd") as GDScript).get_script_constant_map()["T"]["goal_line"])
	var fp := (1.0 if me == 0 else -1.0) * (goal_line - float(band["metres"]))
	sim._offer_set_shot(me, fp, shooter, defender, band, feeder)
	m.call("_show_moment")
	return m


func _run() -> void:
	var club := "COL"
	var venue := ""
	var bands := ["close", "front", "angle", "pocket", "long"]
	var topdown := false
	var clip := false
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		match str(a[i]):
			"--topdown":
				topdown = true
			"--clip":
				clip = true
		if i + 1 >= a.size():
			continue
		match str(a[i]):
			"--out":
				_out = str(a[i + 1])
			"--club":
				club = str(a[i + 1])
			"--venue":
				venue = str(a[i + 1])
			"--bands":
				bands = Array(str(a[i + 1]).split(","))
			"--size":
				var wh := str(a[i + 1]).split("x")
				W = int(wh[0])
				H = int(wh[1])
	await process_frame
	_MS = load("res://scripts/sim/MatchSim.gd")
	_VG = load("res://scripts/ui/match/VignetteGround.gd")
	var state = root.get_node("GameState")
	state.autosave_enabled = false
	state.save_path = "user://capture_ss.save"
	state.settings_path = "user://capture_ss_settings.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(W, H))
	root.size = Vector2i(W, H)
	await _frames(10)
	var Stoppage = load("res://scripts/ui/match/StoppageVignette.gd")
	Stoppage.log_frames = true
	Stoppage.frame_log.clear()
	var plan := []
	for key in bands:
		var m: Control = await _stage(club, str(key), venue)
		if m == null:
			print("NO MATCH for ", key)
			continue
		var vig = m.find_child("DecisionVignette", true, false)
		if vig == null:
			print("NO SCENE for ", key)
			m.queue_free()
			continue
		if clip:
			await _clip(m, vig, "%s_%s_clip" % [_out, key])
		else:
			vig.finish_now()
			await _frames(40)
		print("TITLE ", key, " ", vig.title)
		print("VENUE ", key, " ", _VG.venue, " goal line ", snappedf(_VG.GOAL_Y, 0.01))
		await _shot("%s_%s.png" % [_out, key])
		if vig.has_method("spot_of"):
			var row: Dictionary = _measure(vig, str(key))
			plan.append(row)
			_frame_line(m, vig, str(key))
		m.queue_free()
		await _frames(4)
	var seen := {}
	for e in Stoppage.frame_log:
		var k := "%s/%s" % [e["anim"], e["facing"]]
		if not seen.has(k):
			seen[k] = {"frames": int(e["frames"]), "max_wanted": 0}
		seen[k]["max_wanted"] = maxi(int(seen[k]["max_wanted"]), int(e["wanted"]))
	for k in seen:
		print("ART ", k, " frames ", seen[k]["frames"], " max wanted ", seen[k]["max_wanted"])
	if topdown and not plan.is_empty():
		await _topdown(plan)
	quit(0)


## Every frame from the cut until the scene has settled on its freeze and the call has slid all
## the way up, and 15 more.
func _clip(m: Control, vig, dir: String) -> void:
	DirAccess.make_dir_recursive_absolute(dir)
	var panel: Control = m.find_child("BounceCall", true, false)
	var margin: Control = panel.get_parent().get_parent() if panel != null else null
	var n := 0
	var after := -1
	while n < 200 and after != 0:
		var img := root.get_viewport().get_texture().get_image()
		img.convert(Image.FORMAT_RGBA8)
		img.save_png("%s/%03d.png" % [dir, n])
		n += 1
		var settled: bool = float(vig.get("_hold")) >= 0.4 and (margin == null or margin.get_theme_constant("margin_bottom") == 0)
		if settled and after < 0:
			after = 15
		elif after > 0:
			after -= 1
		await process_frame
	print("CLIP ", dir, " ", n, " frames")


## Where the scene stood everyone, read back from the scene itself (oval metres).
func _measure(vig, key: String) -> Dictionary:
	var goal := Vector2(0.0, _VG.GOAL_Y)
	var k: Dictionary = vig.token_of("kicker")
	var d: Dictionary = vig.token_of("on_the_mark")
	var kick: Vector2 = vig.spot_of(k)
	var mark: Vector2 = vig.spot_of(d) if not d.is_empty() else Vector2.INF
	var cam: Vector2 = vig.camera_spot()
	var metres: float = 0.0
	for b in _MS.SET_BANDS_ON:
		if str(b["key"]) == key:
			metres = float(b["metres"])
	var off := goal - kick
	var angle := rad_to_deg(atan2(absf(off.x), off.y))
	# The arc lies between him and the goal when he stands outside it.
	var arc_between: bool = kick.distance_to(goal) > _VG.ARC
	# The camera against his line to the goals: how far back from him, how far to the side.
	var ahead := off.normalized()
	var rel := cam - kick
	print("MEASURE %s label %.0f m | kicker %.1f m, %.1f deg | mark %s | camera %.1f m behind him, %.1f m across | arc between: %s" % [
			key, metres, kick.distance_to(goal), angle,
			("%.1f m" % mark.distance_to(goal)) if mark != Vector2.INF else "none",
			-rel.dot(ahead), absf(rel.cross(ahead)), "yes" if arc_between else "no"])
	# The ground as the scene drew it (the statics go back to the default ground with the match).
	return {"key": key, "metres": metres, "kick": kick, "mark": mark, "cam": cam,
			"ground": [float(_VG.A), float(_VG.L), float(_VG.GOAL_Y), str(_VG.venue)]}


## Where things sit in the capture, in its own pixels: the title bar's foot, the call
## panel's top, each man's head and feet, and the goal posts' feet and tops.
func _frame_line(m: Control, vig, key: String) -> void:
	var s: float = float(W) / root.get_visible_rect().size.x
	var o: Vector2 = vig.get_global_rect().position
	var at := func(p: Vector3) -> Vector2:
		return (o + Vector2(p.x, p.y)) * s
	var panel: Control = m.find_child("BounceCall", true, false)
	var line := "FRAME %s | bar foot %.0f | panel top %.0f" % [key, (o.y + vig.size.y * 0.075) * s,
			panel.get_global_rect().position.y * s if panel != null else -1.0]
	for role in ["kicker", "on_the_mark"]:
		var t: Dictionary = vig.token_of(role)
		if t.is_empty():
			continue
		var pos: Vector2 = vig.call("_pos", t)
		var feet: Vector2 = at.call(vig.call("_project", pos, vig.call("_lift", t)))
		var head: Vector2 = at.call(vig.call("_project", pos, float(vig.call("_lift", t)) + float(vig.call("_figure_top", t))))
		line += " | %s feet %.0f,%.0f head %.0f" % [role, feet.x, feet.y, head.y]
	var cam = vig.ground_cam()
	for x in [-0.5, 0.5]:
		var foot: Vector2 = at.call(cam.oval(Vector2(x * _VG.GOAL_GAP, _VG.GOAL_Y)))
		var tip: Vector2 = at.call(cam.oval(Vector2(x * _VG.GOAL_GAP, _VG.GOAL_Y), _VG.GOAL_H))
		line += " | post %.0f,%.0f top %.0f" % [foot.x, foot.y, tip.y]
	for x in [-1.5, 1.5]:
		var foot: Vector2 = at.call(cam.oval(Vector2(x * _VG.GOAL_GAP, _VG.GOAL_Y)))
		line += " | behind post %.0f" % foot.x
	var screen: Rect2 = _VG.screen_rect(cam)
	if not screen.has_area():
		line += " | big screen behind the camera"
	else:
		line += " | big screen top %.0f %s" % [(o.y + screen.position.y) * s,
				"left out" if bool(vig.call("_screen_board", cam).get("off", false)) else "shown"]
	print(line)


## The attacking end from above, to scale: the boundary, the goal line, the square, the
## posts, the 50 m arc, and each spot's kicker (filled), mark (ring) and camera (square),
## with a 10 m scale bar.
func _topdown(plan: Array) -> void:
	var c := Control.new()
	root.add_child(c)
	c.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	await _frames(2)
	var cw: float = root.get_visible_rect().size.x
	var ch: float = root.get_visible_rect().size.y
	var ground: Array = plan[0]["ground"]
	var ga: float = ground[0]
	var gl: float = ground[1]
	var gy: float = ground[2]
	print("TOPDOWN canvas %.0fx%.0f | ground %s %.1f by %.1f m, goal line %.2f" % [cw, ch, ground[3], gl * 2.0, ga * 2.0, gy])
	# From 6 m behind the goal line to 70 m out, 32 m either side of the goals.
	var px: float = minf((cw - 24.0) / 64.0, (ch - 150.0) / 76.0)     # pixels per metre
	var top := 96.0
	var y0: float = gy + 6.0               # the oval y at the top of the drawing
	var to_px := func(p: Vector2) -> Vector2:
		return Vector2(cw * 0.5 + p.x * px, top + (y0 - p.y) * px)
	var font: Font = ThemeDB.fallback_font
	var fs := int(cw / 30.0)
	c.draw.connect(func() -> void:
		c.draw_rect(Rect2(0, 0, cw, ch), Color(0.12, 0.3, 0.14), true)
		var ring := []
		for i in range(721):
			var t := TAU * i / 720.0
			ring.append(to_px.call(Vector2(cos(t) * ga, sin(t) * gl)))
		c.draw_polyline(PackedVector2Array(ring), Color.WHITE, 1.5)
		var g: float = _VG.GOAL_GAP
		c.draw_line(to_px.call(Vector2(-1.5 * g, gy)), to_px.call(Vector2(1.5 * g, gy)), Color.WHITE, 1.5)
		c.draw_polyline(PackedVector2Array([to_px.call(Vector2(-0.5 * g, gy)), to_px.call(Vector2(-0.5 * g, gy - 9.0)),
				to_px.call(Vector2(0.5 * g, gy - 9.0)), to_px.call(Vector2(0.5 * g, gy))]), Color.WHITE, 1.5)
		for i in [-1.5, -0.5, 0.5, 1.5]:
			c.draw_circle(to_px.call(Vector2(i * g, gy)), 3.0 if absf(i) < 1.0 else 2.0, Color.WHITE)
		var arc := []
		for i in range(181):
			var t := PI * i / 180.0
			arc.append(to_px.call(Vector2(cos(t) * 50.0, gy - sin(t) * 50.0)))
		c.draw_polyline(PackedVector2Array(arc), Color(1, 1, 1, 0.8), 1.5)
		c.draw_string(font, to_px.call(Vector2(2.0, gy - 50.0)) + Vector2(0.0, fs + 6.0), "50 m arc", HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color.WHITE)
		# Scale bar: 10 m.
		var sb := Vector2(16.0, ch - 30.0)
		c.draw_line(sb, sb + Vector2(10.0 * px, 0.0), Color.WHITE, 3.0)
		c.draw_string(font, sb + Vector2(0.0, -8.0), "10 m", HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color.WHITE)
		var goal := Vector2(0.0, gy)
		for row in plan:
			var k: Vector2 = row["kick"]
			c.draw_line(to_px.call(k), to_px.call(goal), Color(1, 1, 1, 0.35), 1.0)
			var cp: Vector2 = to_px.call(row["cam"])
			c.draw_rect(Rect2(cp - Vector2(3, 3), Vector2(6, 6)), Color(0.6, 0.85, 1.0), true)
			if row["mark"] != Vector2.INF:
				c.draw_arc(to_px.call(row["mark"]), 4.5, 0.0, TAU, 16, Color(1.0, 0.4, 0.3), 1.5)
			c.draw_circle(to_px.call(k), 4.0, Color(1.0, 0.85, 0.2))
			# Names sit left of the dot, clear of the line to the goals and the arc; the pocket
			# one goes under and right of it, where its own line would run through it.
			var label := "%s %.1f m" % [row["key"], k.distance_to(goal)]
			var tw := font.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
			var dot: Vector2 = to_px.call(k)
			var at := dot + Vector2(8.0, fs + 6.0) if k.x > 5.0 and k.y > gy - 30.0 else dot + Vector2(-tw - 12.0, fs * 0.35)
			c.draw_string(font, at, label, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color.WHITE)
		var venue: String = str(ground[3]) if str(ground[3]) != "" else "default ground"
		c.draw_string(font, Vector2(14, 26), "Set-shot spots from above, to scale", HORIZONTAL_ALIGNMENT_LEFT, cw - 28.0, fs + 2, Color.WHITE)
		c.draw_string(font, Vector2(14, 48), "%s; metres from the middle of the goal line" % venue,
				HORIZONTAL_ALIGNMENT_LEFT, cw - 28.0, fs, Color(1, 1, 1, 0.85))
		c.draw_string(font, Vector2(14, 68), "dot kicker, ring man on the mark, square camera",
				HORIZONTAL_ALIGNMENT_LEFT, cw - 28.0, fs, Color(1, 1, 1, 0.85))
	)
	c.queue_redraw()
	await _frames(4)
	await _shot("%s_topdown.png" % _out)
