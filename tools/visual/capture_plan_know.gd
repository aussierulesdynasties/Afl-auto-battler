extends SceneTree
## Plan familiarity, for the lead's check and the director's look. Needs a real renderer:
##   godot --path . --script tools/visual/capture_plan_know.gd -- --out /tmp/pk --club FRE [--size 1280x720]
## Writes <out>_drill.png (a Game plan block and the plans it can drill, with how
## well the side knows each), <out>_drill_two.png (two plans drilled),
## <out>_tiles.png (the pre-match plan tiles, "Plan fluency"), <out>_break.png
## (the break's plan call and the line under it). The levels shown are set by this
## tool for the look (contest low, controlled medium); it is not a balance read.
## <out>_part.png (row 126): a 2-week block split between two plans, each button saying
## how far along it goes, and a plan already part way from last year.

var W := 390
var H := 844


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
	var out := "/tmp/pk"
	var club := "FRE"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		if str(a[i]) == "--club":
			club = str(a[i + 1])
		if str(a[i]) == "--size":
			var wh := str(a[i + 1]).split("x")
			W = int(wh[0])
			H = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_plan_know.save"
	state.settings_path = "user://capture_plan_know_settings.cfg"
	state.reset()
	state.career_seed = 4127
	state.replay_seed = 4127
	state.set_setting("seen_weekly_loop_intro", true)
	state.set_setting("seen_training_intro", true)
	state.set_setting("seen_coaching_intro", true)
	if W >= 760:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		DisplayServer.window_set_size(Vector2i(W, H))
		for i in range(10):
			await process_frame
		var factor := float(W) / maxf(1.0, root.get_visible_rect().size.x)
		if factor > 1.05:
			DisplayServer.window_set_size(Vector2i(int(W * factor), int(H * factor)))
			for i in range(10):
				await process_frame
	else:
		DisplayServer.window_set_size(Vector2i(W, H))
		root.size = Vector2i(W, H)
	for i in range(3):
		await process_frame
	state.start_season(club, db.club_list(club))
	state.set_club_plan("attacking")
	_vs(state, club, "STK" if club == "FRE" else "WBD")
	state.open_preseason()
	# For the look: a side that knows its plans unevenly.
	state.plan_known[club]["defensive"] = 0
	state.plan_known[club]["controlled"] = 1
	state.plan_known[club]["defensive"] = 1
	root.get_node("Router").go("hub")
	await _frames(10)
	await _press("Focus0_plan")
	await _press("Drill0_contest")
	await _press("Drill0_attacking")
	await _scroll_to("BlockCost_0")
	await _shot(out + "_drill.png")
	await _press("Drill0_defensive")
	await _scroll_to("BlockCost_0")
	await _shot(out + "_drill_two.png")
	await _press("Drill0_defensive")
	# Row 126: the two-week block split between two plans, and a plan part way.
	state.set_preseason_block(0, "solid", "running")
	state.set_preseason_block(1, "solid", "plan")
	state.set_preseason_drills(1, ["contest", "controlled"])
	state.plan_known[club]["defensive"] = 0.5
	root.get_node("Router").go("hub")
	await _frames(10)
	await _scroll_to("BlockCost_1")
	await _shot(out + "_part.png")
	state.plan_known[club]["defensive"] = 1
	state.set_preseason_block(1, "solid", "running")
	state.set_preseason_block(0, "solid", "plan")
	state.set_preseason_drills(0, ["contest"])
	root.get_node("Router").go("hub")
	await _frames(10)
	await _press("PreSeasonSim")
	await _frames(6)
	await _press("PreSeasonSimGo")
	await _frames(20)
	print("scene ", current_scene.name, " after: contest ", state.plan_level(club, "contest"), " attacking ",
			state.plan_level(club, "attacking"))
	state.plan_known[club]["controlled"] = 1.5
	state.plan_known[club]["defensive"] = 0
	root.get_node("Router").go("coaching")
	await _frames(12)
	await _scroll_to("ClubPlan")
	await _shot(out + "_tiles.png")
	if state.prepare_interactive_match():
		root.get_node("Router").go("match")
		await _frames(40)
		await _press("PlanPicker_defensive")
		await _scroll_to("PlanNote")
		await _shot(out + "_break.png")
	quit(0)


## Round 1 against a coloured club (never Collingwood on a capture): swap the
## opponent with whoever plays `opp`.
func _vs(state, club: String, opp: String) -> void:
	var mine: Dictionary = {}
	var theirs: Dictionary = {}
	for m in state.season.fixture[0]:
		if str(m["home"]) == club or str(m["away"]) == club:
			mine = m
		if str(m["home"]) == opp or str(m["away"]) == opp:
			theirs = m
	if mine.is_empty() or theirs.is_empty() or mine == theirs:
		return
	var old := str(mine["away"]) if str(mine["home"]) == club else str(mine["home"])
	for k in ["home", "away"]:
		if str(theirs[k]) == opp:
			theirs[k] = old
		if str(mine[k]) == old:
			mine[k] = opp


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame
	# A windowed run swaps screens under the cover, on a thread: wait it out.
	var wipe: Node = root.get_node_or_null("ScreenTransition")
	var waited := 0
	while wipe != null and bool(wipe.get("busy")) and waited < 1800:
		await process_frame
		waited += 1


## Bring a node into view in whatever scroll holds it.
func _scroll_to(node_name: String) -> void:
	await _frames(4)
	var n: Node = current_scene.find_child(node_name, true, false)
	var p: Node = n.get_parent() if n != null else null
	while p != null and not (p is ScrollContainer):
		p = p.get_parent()
	if p != null:
		(p as ScrollContainer).ensure_control_visible(n as Control)
	elif n == null:
		print("MISSING ", node_name)
	await _frames(4)


func _press(node_name: String) -> void:
	await _frames(3)
	var b: Node = current_scene.find_child(node_name, true, false)
	if b is Button:
		(b as Button).emit_signal("pressed")
	else:
		print("MISSING ", node_name)
	await _frames(3)
