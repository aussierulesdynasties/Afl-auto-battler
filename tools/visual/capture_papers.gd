extends SceneTree
## The papers stop (pre-season, week 8), for the lead's check and the director's look.
## Needs a real renderer:
##   godot --path . --script tools/visual/capture_papers.gd -- --out /tmp/pap --club FRE [--size 1280x720] [--seed 4127]
## Writes <out>_<kind>.png for each story (finish, pressure, breakout) as it
## opens, <out>_<kind>_low.png (scrolled to the ladder), and <out>_finish_answered.png
## (the club talked up). The story kind is forced for the look only.
## --real keeps the paper's own ladder (the practice matches' nudge and all) and
## writes <out>_real.png and <out>_real_low.png, and on a phone <out>_ladder_NN.png
## (the ladder three clubs further down each time, so every blurb can be read); --want-win N tries seeds from
## --seed up until the club won its practice match by N points or more.

var W := 390
var H := 844
var _seed := 4127
var _risk := -1.0
var _real := false
var _want_win := -999


func _initialize() -> void:
	_run.call_deferred()


func _shot(path: String) -> void:
	for i in range(8):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if W >= 760 and img.get_width() != W:
		img.resize(W, H, Image.INTERPOLATE_LANCZOS)
	img.save_png(path)
	print("wrote ", path)


func _run() -> void:
	var out := "/tmp/pre"
	var club := "FRE"
	var a := OS.get_cmdline_user_args()
	# Every argument is read, the last one too (a trailing --real); a flag that
	# takes a value reads "" when none follows it.
	for i in range(a.size()):
		var flag := str(a[i])
		var value := str(a[i + 1]) if i + 1 < a.size() else ""
		if flag == "--real":
			_real = true
		if value == "":
			continue
		if flag == "--out":
			out = value
		if flag == "--club":
			club = value
		if flag == "--risk":
			# A bigger Heavy-week risk than the game's, so the "Hurt in training"
			# list is sure to show (for the look only; never a balance read).
			_risk = float(value)
		if flag == "--art" and value == "off":
			# The stops without their pictures, as they were (the before shot).
			load("res://scripts/ui/UiArt.gd").set("dir", "res://assets/ui/none")
		if flag == "--want-win":
			_want_win = int(value)
		if flag == "--seed":
			_seed = int(value)
		if flag == "--size":
			var wh := value.split("x")
			if wh.size() == 2:
				W = int(wh[0])
				H = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_preseason.save"
	state.settings_path = "user://capture_preseason_settings.cfg"
	state.show_real_names = true
	state.reset()
	state.career_seed = _seed
	state.replay_seed = _seed
	state.set_setting("seen_weekly_loop_intro", true)
	state.set_setting("seen_training_intro", true)
	state.set_setting("seen_preseason_intro", true)
	# The canvas a player's screen gives the game, whatever this machine's display density.
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(W, H))
	for i in range(10):
		await process_frame
	var layout = root.get_node("ScreenLayout")
	var density: float = layout.desktop_density(Vector2(root.size), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0)
	layout.ui_scale = 1.0 / maxf(1.0, density)
	layout._update_scale()
	for i in range(10):
		await process_frame
	print("canvas ", root.get_visible_rect().size)
	for i in range(3):
		await process_frame
	var tries := 0
	while true:
		state.reset()
		state.career_seed = _seed
		state.replay_seed = _seed
		state.start_season(club, db.club_list(club))
		state.open_preseason()
		if _want_win == -999:
			break
		var g := 0
		while state.preseason_active() and state.preseason_stop() != "papers" and g < 12:
			g += 1
			state.preseason_advance()
		var margin := int((state.preseason.get("practice_margins", {}) as Dictionary).get(club, -999))
		print("seed ", _seed, " practice margin ", margin)
		tries += 1
		if margin >= _want_win or tries >= 40:
			break
		_seed += 1
	state.set_setting("seen_weekly_loop_intro", true)
	state.set_setting("seen_training_intro", true)
	state.set_setting("seen_preseason_intro", true)
	if _risk >= 0.0:
		load("res://scripts/sim/PreSeason.gd").data()["heavy_week_injury"] = _risk
	for m in state.season.fixture[0]:
		if str(m["home"]) == club or str(m["away"]) == club:
			print("round 1: ", m["home"], " v ", m["away"])
	# Press on to week 8.
	var guard := 0
	while state.preseason_active() and state.preseason_stop() != "papers" and guard < 12:
		guard += 1
		state.preseason_advance()
	print("stop ", state.preseason_stop())
	if _real:
		var rec0: Dictionary = state.papers_record()
		print("seed ", _seed, " margin ", (state.preseason.get("practice_margins", {}) as Dictionary).get(club, "none"),
				" pred ", rec0.get("pred"), " moves ", rec0.get("moves"), " order ", rec0.get("order"))
		root.get_node("Router").go("hub")
		if not await _wait_for("PapersLadder"):
			return
		# Past the loading card and the wipe into the screen.
		await create_timer(3.0).timeout
		await _shot(out + "_real.png")
		await _scroll(true)
		await create_timer(0.5).timeout
		await _shot(out + "_real_low.png")
		# The ladder a few clubs at a time, each block of rows at the top of the
		# page, with every club's power-ranking blurb (director, 2026-11-12).
		for i in ([] if W >= 900 else [0, 3, 6, 9, 12, 15]):
			await _scroll_to("PapersRow_%d" % i)
			await create_timer(0.3).timeout
			await _shot(out + "_ladder_%02d.png" % (i + 1))
		print("blurbs ", state.papers_blurbs())
		quit(0)
		return
	# For the look only: the paper has the club 13th, so the ladder and the words agree.
	var order: Array = state.papers_record()["order"]
	order.erase(club)
	order.insert(12, club)
	for kind in ["finish", "pressure", "breakout"]:
		var rec: Dictionary = state.papers_record()
		rec["kind"] = kind
		rec["pred"] = 13
		rec["claim"] = 0
		rec["answered"] = false
		rec["result"] = ""
		rec["pid"] = state._papers_breakout() if kind == "breakout" else ""
		root.get_node("Router").go("hub")
		if not await _wait_for("PapersTitle"):
			return
		print("scene ", current_scene.name, " ", kind)
		await _shot(out + "_" + kind + ".png")
		await _scroll(true)
		await _shot(out + "_" + kind + "_low.png")
		await _scroll(false)
	var rec2: Dictionary = state.papers_record()
	rec2["kind"] = "finish"
	rec2["pid"] = ""
	rec2["answered"] = false
	root.get_node("Router").go("hub")
	if not await _wait_for("Papers_2"):
		return
	await _press("Papers_2")
	await _frames(6)
	await _shot(out + "_finish_answered.png")
	quit(0)


## Waits (10 s of frames at most) for the screen to open with `node_name` on
## it. When no scene opens, or the node never shows, it says so and quits with
## an error rather than hanging or shooting an empty window.
func _wait_for(node_name: String) -> bool:
	var wait := 0
	while (current_scene == null or current_scene.find_child(node_name, true, false) == null) and wait < 600:
		wait += 1
		await process_frame
	if current_scene == null or current_scene.find_child(node_name, true, false) == null:
		push_error("capture_papers: %s never showed (%s)" % [node_name,
				"no scene opened" if current_scene == null else "scene %s" % current_scene.name])
		quit(1)
		return false
	await _frames(10)
	return true


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _scroll(to_foot: bool) -> void:
	await _frames(3)
	var page: Node = current_scene.find_child("PreSeasonPage", true, false) if current_scene != null else null
	var sc := page.get_parent() as ScrollContainer if page != null else null
	if sc != null:
		sc.scroll_vertical = int(sc.get_v_scroll_bar().max_value) if to_foot else 0
	await _frames(3)


## Scroll the page so `node_name` sits at the top of it.
func _scroll_to(node_name: String) -> void:
	await _frames(3)
	var page: Node = current_scene.find_child("PreSeasonPage", true, false) if current_scene != null else null
	var sc := page.get_parent() as ScrollContainer if page != null else null
	var row := current_scene.find_child(node_name, true, false) as Control if current_scene != null else null
	if sc != null and row != null:
		sc.scroll_vertical = int(row.global_position.y - (page as Control).global_position.y) - 8
	await _frames(3)


func _press(node_name: String) -> void:
	await _frames(3)
	var b: Node = current_scene.find_child(node_name, true, false) if current_scene != null else null
	if b is Button:
		(b as Button).emit_signal("pressed")
	else:
		print("MISSING ", node_name)
	await _frames(3)
