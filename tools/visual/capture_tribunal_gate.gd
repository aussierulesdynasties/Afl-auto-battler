extends SceneTree
## Visual review tool for the hub's Tribunal card with its Gain / Cost rows
## (row T1.R26 C1, director 2026-11-10 "Build as shown"). Windowed:
##   godot --windowed --path . --script tools/visual/capture_tribunal_gate.gd -- --out <prefix> --size 390x844
## Melbourne, one of its players suspended two weeks for rough conduct. Writes
## <out>.png with the Tribunal card scrolled into view. Never touches a real save.

var _w := 390
var _h := 844


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	var out := "tribunal_gate"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	var feel = load("res://scripts/ui/Feel.gd")
	state.autosave_enabled = false
	state.save_path = "user://capture_tribunal_gate.save"
	state.settings_path = "user://capture_tribunal_gate.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	state.show_real_names = false
	UK.apply_appearance("dark")
	root.size = Vector2i(_w, _h)
	DisplayServer.window_set_size(Vector2i(_w, _h))
	feel.force_phone = _w < _h
	state.reset()
	state.replay_seed = 2027
	state.start_season("MEL", db.club_list("MEL"))
	state.tutorials = false
	var p: Dictionary = state.my_list[2]
	state.last_mro = [{"id": str(p["id"]), "name": db.player_display_name(p), "club": "MEL",
			"outcome": "suspension", "weeks": 2, "reason": "rough conduct", "round": 1}]
	for card in state.week_events:
		(card as Dictionary)["popped"] = true
	var hub = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _frames(10)
	await create_timer(0.8).timeout
	var line: Control = hub.find_child("TribunalLine", true, false)
	if line == null:
		push_error("no TribunalLine on the hub")
		quit(1)
		return
	var p_node: Node = line.get_parent()
	while p_node != null and not (p_node is ScrollContainer):
		p_node = p_node.get_parent()
	var cost: Control = hub.find_child("TribunalCost", true, false)
	if p_node != null:
		# The whole card in view: its last row (the buttons, else Cost) at the bottom.
		var sc := p_node as ScrollContainer
		var card: Control = line.get_parent() as Control
		var last: Control = card.get_child(card.get_child_count() - 1) as Control if card != null else cost
		sc.ensure_control_visible(last if last != null else cost)
		await _frames(4)
		sc.scroll_vertical += 24
	await create_timer(0.6).timeout
	print("TRIBUNAL line y=%.0f cost bottom=%.0f of %d" % [line.get_global_rect().position.y,
			cost.get_global_rect().end.y if cost != null else -1.0, _h])
	await _save("%s.png" % out)
	quit(0)


func _save(path: String) -> void:
	await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if img.save_png(path) != OK:
		push_error("could not save " + path)
	print("wrote ", path)
