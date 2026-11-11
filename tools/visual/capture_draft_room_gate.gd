extends SceneTree
## Review capture for the draft list gate (director, 2026-11-12, "Must make
## room"), dark, 360x740, Melbourne with one open senior spot for its picks:
##   godot --path . --script tools/visual/capture_draft_room_gate.gd -- --out /tmp/gate
## Needs a real renderer and a window. Writes <out>_1_gate.png (the gate the
## draft button opens), <out>_2_delist.png and <out>_3_trade.png (where its two
## routes land).

const W := 360
const H := 740
const CLUB := "MEL"


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
	var out := "/tmp/gate"
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
	state.set_setting("seen_weekly_loop_intro", true)
	state.replay_seed = 2027
	state.reset()
	state.postseason_intro_seen = true
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	state.start_season(CLUB, db.club_list(CLUB))
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
	print("short=", state.draft_room_short(), " spots=", state.draft_list_spots())
	for step in [["", "_1_gate.png"], ["DraftRoomDelist", "_2_delist.png"], ["DraftRoomTrade", "_3_trade.png"]]:
		var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
		root.add_child(hub)
		for i in range(8):
			await process_frame
		hub.call("_on_intake_draft")
		for i in range(4):
			await process_frame
		if str(step[0]) != "":
			var b = hub.find_child(str(step[0]), true, false)
			if b != null:
				b.emit_signal("pressed")
			hub.queue_free()
			for i in range(20):
				await process_frame
		await _shot(out + str(step[1]))
		if is_instance_valid(hub):
			hub.queue_free()
		var cur = current_scene
		if cur != null and is_instance_valid(cur):
			cur.queue_free()
		for i in range(4):
			await process_frame
	quit(0)
