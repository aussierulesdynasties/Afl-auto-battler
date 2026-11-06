extends SceneTree
## Review capture for the full-list draft fix (director report 2026-11-07: "I
## had 4 picks in the draft but it only let me use two"), dark, 390x844,
## Collingwood with a senior list one short of the cap:
##   godot --path . --script tools/visual/capture_draft_spots.gd -- --out /tmp/spots
## Needs a real renderer and a window (keep it off screen with an override.cfg).
## Writes <out>_1_sheet.png (the sheet the draft button opens), <out>_2_passed.png
## (the draft board after a pick passed) and <out>_3_your_picks.png (Your picks).

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
	var out := "/tmp/spots"
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
	state.replay_seed = 2027
	state.reset()
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	state.start_season("COL", db.club_list("COL"))
	var s = state.season
	s.round_index = s.fixture.size()
	s.finals = {"done": true, "premier": "CAR", "runner_up": "ESS"}
	state.open_offseason()
	var rl = load("res://scripts/state/RookieList.gd")
	var n := 0
	while rl.senior_count(state.my_list) < rl.SENIOR_SPOTS - 1 and n < 40:
		var copy: Dictionary = (state.my_list[n % state.my_list.size()] as Dictionary).duplicate(true)
		copy["id"] = "pad_%d" % n
		copy["rookie_list"] = ""
		state.my_list.append(copy)
		n += 1
	for p in state.my_list:
		p["contract_years"] = 3
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	for i in range(8):
		await process_frame
	hub.call("_on_intake_draft")
	await _shot(out + "_1_sheet.png")
	hub.queue_free()
	state.begin_intake_draft()
	var draft = state.draft
	for i in range(400):
		if draft.is_finished() or not draft.user_passed.is_empty():
			break
		if draft.is_user_turn():
			draft.pick_for_me()
		else:
			draft.auto_until_user_turn()
	var ui: Control = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	for i in range(8):
		await process_frame
	var done = ui.find_child("MeetingDone", true, false)
	if done != null:
		done.emit_signal("pressed")
	await _shot(out + "_2_passed.png")
	ui.call("_select_tab", "squad")
	await _shot(out + "_3_your_picks.png")
	quit(0)
