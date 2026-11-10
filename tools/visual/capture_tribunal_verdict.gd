extends SceneTree
## Visual review tool for the Tribunal verdict sheet (row 146) on the hub on a
## phone (390x844), Fremantle:
##   godot --path . --script tools/visual/capture_tribunal_verdict.gd -- --out /tmp/tribunal
## Writes <out>_sheet.png: the hub's Tribunal card, a won challenge, a lost
## challenge (the appeal still open), a lost appeal.

const W := 390
const H := 844


func _initialize() -> void:
	_run.call_deferred()


func _shot() -> Image:
	for i in range(8):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	return img


func _press(hub: Node, text: String) -> void:
	for b in hub.find_children("*", "Button", true, false):
		if (b as Button).text == text and (b as Button).is_visible_in_tree():
			(b as Button).pressed.emit()
			return
	push_error("No button: " + text)


func _run() -> void:
	var out := "/tmp/tribunal"
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
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	# [weeks, tribunal roll, appeal roll, buttons to press]
	var arms := [
		[2, 0.99, 0.99, []],
		[2, 0.0, 0.99, ["Challenge at Tribunal"]],
		[2, 0.99, 0.99, ["Challenge at Tribunal"]],
		[2, 0.99, 0.99, ["Challenge at Tribunal", "Done", "Appeal to Appeals Board"]],
	]
	var shots := []
	for arm in arms:
		state.reset()
		state.career_seed = 4403
		state.replay_seed = 4403
		state.set_setting("seen_weekly_loop_intro", true)
		state.start_season("FRE", db.club_list("FRE"))
		# No week card over the hub: the Tribunal card is what this shows.
		state.week_events = []
		var p: Dictionary = state.my_list[0]
		state._process_discipline([{"home": "FRE", "away": "MEL", "reports": [{"side": 0,
				"id": str(p["id"]), "name": db.player_display_name(p), "victim_id": "v1",
				"victim_name": "Victim", "reason": "rough conduct", "outcome": "suspension",
				"weeks": int(arm[0]), "tribunal_roll": float(arm[1]), "appeal_roll": float(arm[2]),
				"challenged": false, "appealed": false}]}])
		var hub = load("res://scenes/HubScene.tscn").instantiate()
		root.add_child(hub)
		for i in range(8):
			await process_frame
		for t in arm[3]:
			_press(hub, str(t))
			for i in range(6):
				await process_frame
		shots.append(await _shot())
		hub.queue_free()
		await process_frame
	var sheet := Image.create(W * shots.size(), H, false, Image.FORMAT_RGBA8)
	for i in range(shots.size()):
		sheet.blit_rect(shots[i], Rect2i(0, 0, W, H), Vector2i(i * W, 0))
	sheet.save_png(out + "_sheet.png")
	quit(0)
