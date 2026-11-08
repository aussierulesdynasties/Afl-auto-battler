extends SceneTree
## Review capture for row 64 (an undrafted prospect's rookie list chance), dark,
## 390x844, Adelaide after its first National Draft:
##   godot --path . --script tools/visual/capture_rookie_chance.gd -- --out /tmp/rookie
## Needs a real renderer and a window (keep it off screen with an override.cfg).
## Writes <out>_1_sheet.png (the Rookie Draft sheet: prospects the National
## Draft passed over) and <out>_2_list.png (your list after you pick one).

const W := 390
const H := 844


func _initialize() -> void:
	_run.call_deferred()


func _shot(path: String) -> void:
	for i in range(10):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png(path)
	print("wrote ", path)


func _run() -> void:
	var out := "/tmp/rookie"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture.save"
	state.settings_path = "user://capture_settings.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	state.tutorials = false
	state.replay_seed = 8801
	state.reset()
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	state.start_season("ADE", db.club_list("ADE"))
	state.season.round_index = state.season.fixture.size()
	state.begin_intake_draft()
	var draft = state.draft
	while not draft.is_finished():
		var c: Dictionary = draft._best_ai_pick(draft.current_club())
		if c.is_empty() or not draft._draft_pick(draft.current_club(), c):
			draft._skip_current_pick()
	state.finish_intake_draft()
	if state.needs_season_wrap():
		state.begin_season_from_wrap()
	var path := "res://scenes/PreSeasonScene.tscn" if state.preseason_active() else "res://scenes/HubScene.tscn"
	var scene: Control = load(path).instantiate()
	root.add_child(scene)
	for i in range(8):
		await process_frame
	await _shot(out + "_1_sheet.png")
	var pool: Array = load("res://scripts/state/MidseasonDraft.gd").pool(state)
	var sheet = scene.get_node_or_null("RookieDraft")
	if sheet != null and not pool.is_empty():
		var btn := sheet.find_child("RookiePick_%s" % str(pool[0]["id"]), true, false) as Button
		if btn != null:
			btn.pressed.emit()
	var rl = load("res://scripts/state/RookieList.gd")
	while rl.waiting(state):
		rl.choose(state, "")
	scene.queue_free()
	var ls: Control = load("res://scenes/ListScene.tscn").instantiate()
	ls.set("_pane", "list")
	root.add_child(ls)
	for i in range(8):
		await process_frame
	var head = ls.find_child("RookieListHead", true, false)
	var scroll := ls.find_child("*", true, false)
	for s in ls.find_children("*", "ScrollContainer", true, false):
		if head != null and (s as ScrollContainer).is_ancestor_of(head):
			scroll = s
			(s as ScrollContainer).ensure_control_visible(head)
	for i in range(4):
		await process_frame
	if head != null and scroll is ScrollContainer:
		(scroll as ScrollContainer).scroll_vertical = int((head as Control).global_position.y
				- (scroll as ScrollContainer).global_position.y + (scroll as ScrollContainer).scroll_vertical - 40)
	await _shot(out + "_2_list.png")
	quit(0)
