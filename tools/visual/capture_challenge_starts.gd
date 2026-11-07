extends SceneTree
## Challenge starts (row 114), every screen they touch, for the director's look:
##   godot --path . --script tools/visual/capture_challenge_starts.gd -- --out DIR [--size 390x844]
## Writes DIR/<W>x<H>_<screen>.png: setup_goal, setup_rebuild, draft_rebuild,
## almanac_goal, rookie_youth, agents_youth, trade_youth.
## Needs a real renderer: run windowed (override.cfg), never --headless.

var W := 390
var H := 844
var out := "/tmp/challenge"
var state
var db


func _initialize() -> void:
	_run.call_deferred()


func _arg(name: String, fallback: String) -> String:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == name:
			return str(a[i + 1])
	return fallback


func _shot(name: String) -> void:
	for i in range(14):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	var path := "%s/%dx%d_%s.png" % [out, W, H, name]
	img.save_png(path)
	print("wrote ", path)


## Scroll every scroll box holding `node` so it sits near the top of the view.
func _show(scene: Node, node_name: String) -> Control:
	await process_frame
	await process_frame
	var node: Control = scene.find_child(node_name, true, false)
	if node == null:
		print("CAPTURE missing ", node_name)
		return null
	for sc in scene.find_children("*", "ScrollContainer", true, false):
		var box := sc as ScrollContainer
		if box.is_visible_in_tree() and box.is_ancestor_of(node):
			var dy := node.get_global_rect().position.y - box.get_global_rect().position.y - 60.0
			box.scroll_vertical += int(maxf(dy, 0.0))
	return node


func _press(scene: Node, node_name: String) -> void:
	var b: Button = scene.find_child(node_name, true, false)
	if b == null:
		print("CAPTURE missing button ", node_name)
		return
	b.pressed.emit()
	await process_frame


func _fresh() -> void:
	state.reset()
	state.career_seed = 2027
	state.replay_seed = 2027
	state.tutorials = false
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)


func _run() -> void:
	out = _arg("--out", out)
	var wh := _arg("--size", "390x844").split("x")
	W = int(wh[0])
	H = int(wh[1])
	DirAccess.make_dir_recursive_absolute(out)
	await process_frame
	state = root.get_node("GameState")
	db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_challenge.save"
	state.settings_path = "user://capture_challenge.cfg"
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	root.size = Vector2i(W, H)
	# No hover tooltips from wherever the real cursor happens to be.
	root.gui_disable_input = true
	DisplayServer.window_set_size(Vector2i(W, H))

	print("CAPTURE stage 1")
	# 1. New career: Your goal, then Rebuild.
	_fresh()
	state.start_season("FRE", db.club_list("FRE"))
	root.get_node("Router").to_main_menu(false)
	for i in range(60):
		await process_frame
		if current_scene != null and current_scene.has_method("_on_new_career"):
			break
	if current_scene == null or not current_scene.has_method("_on_new_career"):
		print("CAPTURE no main menu")
		quit(1)
		return
	current_scene._on_new_career()
	await _press(current_scene, "StartMode_real")
	await _press(current_scene, "Challenge_goal")
	await _show(current_scene, "Challenge_none")
	await _shot("setup_goal")
	await _press(current_scene, "Challenge_rebuild")
	await _show(current_scene, "Challenge_none")
	await _shot("setup_rebuild")
	current_scene.queue_free()
	await process_frame

	print("CAPTURE stage 2")
	# 2. Rebuild: the 2026 National Draft board with the rule on it.
	_fresh()
	state.challenge = {"kind": "rebuild"}
	state.begin_real_lists()
	var ds: Control = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ds)
	for i in range(6):
		await process_frame
	await _press(ds, "MeetingDone")
	await _show(ds, "ChallengeRule")
	await _shot("draft_rebuild")
	ds.queue_free()
	await process_frame

	print("CAPTURE stage 3")
	# 3. Your goal (300 games): the coach card mid-season.
	_fresh()
	state.start_season("GEE", db.club_list("GEE"))
	state.challenge = {"kind": "goal", "goal": "coach_300", "met_year": 0}
	for i in range(6):
		state.advance()
	var alm: Control = load("res://scenes/AlmanacScene.tscn").instantiate()
	root.add_child(alm)
	await _show(alm, "CoachLine")
	await _shot("almanac_goal")
	alm.queue_free()
	await process_frame

	print("CAPTURE stage 4")
	# 4. Youth only: the Rookie Draft sheet with over-24 free agents in it.
	state.challenge = {"kind": "youth"}
	var vets := []
	for code in ["ADE", "SYD"]:
		var src: Dictionary = db.club_list(code)[0].duplicate(true)
		src["id"] = "capture_vet_" + code
		src["age"] = 29.0
		src["overall"] = 90
		src["club"] = ""
		src["released_by"] = code
		vets.append(src)
		state.free_agents.append(src)
	state.rookie_draft = {"year": state.season_year, "order": [state.my_club], "next": 0, "round": 1, "done": false, "picks": []}
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await process_frame
	if hub.get_node_or_null("RookieDraft") == null:
		hub._show_week_ask()
	await _shot("rookie_youth")
	print("CAPTURE rookie barred lines: ", hub.find_children("ChallengeWhy_*", "", true, false).size())
	hub.queue_free()
	await process_frame
	for v in vets:
		state.free_agents.erase(v)
	state.rookie_draft = {}

	print("CAPTURE stage 5")
	# 5. Youth only, off-season: free agents and the trade builder.
	state.season.round_index = state.season.fixture.size()
	state.ensure_finals()
	while not state.season.is_season_over():
		state.advance()
	state.open_offseason()
	var off: Control = load("res://scenes/OffseasonScene.tscn").instantiate()
	root.add_child(off)
	await process_frame
	await _press(off, "Tab_agents")
	await _show(off, "FreeAgentBarred")
	await _shot("agents_youth")
	await _press(off, "Tab_trade")
	off._trade_club = "ADE"
	off._build()
	await process_frame
	await _press(off, "TradeSide_theirs")
	var first := ""
	for p in state.season.lists.get("ADE", []):
		if load("res://scripts/state/Challenge.gd").short_tag(state, p) != "":
			first = "Their_" + str(p["id"])
			break
	if first != "":
		await _show(off, first)
	await _shot("trade_youth")
	quit(0)
