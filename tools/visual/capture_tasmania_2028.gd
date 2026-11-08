extends SceneTree
## Take Tasmania from the real 2026 lists (director, 2026-11-09). Needs a real renderer:
##   godot --path . --resolution 390x844 --windowed --script tools/visual/capture_tasmania_2028.gd -- --out <dir>
## Writes tas_1_choose, tas_2_sheet, tas_3_before_draft, tas_4_board.

var out := "C:/Users/DANTE/Documents/GitHub/afl-wt/caps/tas-2028"


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		if str(a[i]) == "--out" and i + 1 < a.size():
			out = str(a[i + 1])
	DirAccess.make_dir_recursive_absolute(out)
	await process_frame
	var state = root.get_node("GameState")
	state.autosave_enabled = false
	state.save_path = "user://capture.save"
	state.settings_path = "user://capture_settings.cfg"
	state.reset()
	root.size = Vector2i(390, 844)
	DisplayServer.window_set_size(Vector2i(390, 844))
	state.set_canberra(false)
	state.begin_real_lists()
	state.set_setting("seen_draft_intro", true)
	var ui: Control = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	await _frames(12)
	var tile: Button = ui.find_child("Choose_TAS", true, false)
	var p := tile.get_parent()
	while p != null:
		if p is ScrollContainer:
			(p as ScrollContainer).ensure_control_visible(tile)
		p = p.get_parent()
	await _frames(6)
	await _shot("tas_1_choose")
	tile.pressed.emit()
	await _frames(8)
	await _shot("tas_2_sheet")
	(ui.find_child("WaitBack", true, false) as Button).pressed.emit()
	await _frames(4)
	ui.queue_free()
	await _frames(2)
	var t0 := Time.get_ticks_msec()
	state.begin_wait_for_club("TAS")
	while state.sim_ahead_step() != "":
		pass
	print("2027 played in %d ms" % (Time.get_ticks_msec() - t0))
	state.choose_sim_ahead_club("TAS")
	print("TAS picks: ", state.draft.upcoming_picks("TAS", 0), " list ", state.my_list.size())
	ui = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	await _frames(14)
	await _shot("tas_3_before_draft")
	for b in ui.find_children("*", "Button", true, false):
		if (b as Button).text == "To the draft":
			(b as Button).pressed.emit()
	await _frames(10)
	await _shot("tas_4_board")
	ui.queue_free()
	await _frames(2)
	quit(0)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(name: String) -> void:
	await process_frame
	await process_frame
	root.get_texture().get_image().save_png("%s/%s_390x844.png" % [out, name])
