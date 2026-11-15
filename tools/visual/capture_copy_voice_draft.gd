extends SceneTree
## Copy voice pass 7 (draft and pre-season, director 2026-11-10: option B) captures, phone portrait
## 390x844, a fresh Fremantle career that never touches a real save. One launch writes every draft
## state whose copy the pass changed, so the same script gives the before (on the base) and the after:
##   godot --path . --script tools/visual/capture_copy_voice_draft.gd -- --out <prefix> [--club FRE]
## Writes <prefix>_<state>.png for: intro_draft, intro_league_draft, intro_combine, intro_preseason,
## pool, player, player_low, squad, order, picks. The pre-season stops come from
## tools/visual/capture_preseason.gd (--size 390x844).

var _out := "copy_voice_draft"
var _club := "FRE"


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			_out = str(a[i + 1])
		elif str(a[i]) == "--club":
			_club = str(a[i + 1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_copy_voice_draft.save"
	state.settings_path = "user://capture_copy_voice_draft.cfg"
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	state.replay_seed = 2027
	state.reset()
	state.start_season(_club, db.club_list(_club))
	state.tutorials = false
	state.season.round_index = state.season.fixture.size()
	state.open_offseason()
	if not state.begin_intake_draft():
		print("no draft")
		quit(1)
		return
	var draft = state.draft
	root.size = Vector2i(390, 844)
	DisplayServer.window_set_size(Vector2i(390, 844))
	var ui: Control = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	await _frames(6)
	var done: Button = ui.find_child("MeetingDone", true, false)
	if done != null:
		done.emit_signal("pressed")
	var guard := 0
	while not draft.is_user_turn() and not draft.is_finished() and guard < 200:
		guard += 1
		draft.auto_until_user_turn()
	ui.call("_refresh")
	await _frames(12)

	# The first-visit intros this pass rewrote, each on the draft room.
	var intro: GDScript = load("res://scripts/ui/FirstVisitIntro.gd")
	for key in ["draft", "league_draft", "combine", "preseason"]:
		var box: Control = intro.call("show", ui, key)
		await _frames(6)
		await _shot("intro_" + key)
		if is_instance_valid(box):
			box.queue_free()
		for n in root.get_tree().get_nodes_in_group(intro.GROUP):
			n.queue_free()
		await _frames(4)

	await _shot("pool")

	# A prospect's sheet: his numbers, then the scouting and testing notes further down.
	var best: Dictionary = {}
	for p in draft.pool:
		if not draft.picked.has(str(p["id"])):
			best = p
			break
	ui.call("_open_player", str(best["id"]))
	await _frames(10)
	await _shot("player")
	await _scroll_to_text(ui, "Testing is")
	await _shot("player_low")
	ui.call("_close_player")
	await _frames(6)

	for tab in ["squad", "order", "picks"]:
		ui.call("_select_tab", tab)
		await _frames(10)
		await _shot(tab)
	quit()


## Scrolls the open sheet so the label starting with `start` sits near the top.
func _scroll_to_text(ui: Node, start: String) -> void:
	var target: Control = null
	for n in ui.find_children("*", "Label", true, false):
		if (n as Label).visible and (n as Label).text.begins_with(start):
			target = n
	if target == null:
		print("missing ", start)
		return
	var sc: Node = target.get_parent()
	while sc != null and not (sc is ScrollContainer):
		sc = sc.get_parent()
	if sc != null:
		(sc as ScrollContainer).scroll_vertical = int(target.global_position.y - (sc as Control).global_position.y
				+ (sc as ScrollContainer).scroll_vertical - 300.0)
	await _frames(8)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(name: String) -> void:
	await _frames(3)
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png("%s_%s.png" % [_out, name])
	print("wrote %s_%s.png" % [_out, name])
