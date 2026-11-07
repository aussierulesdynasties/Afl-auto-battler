extends SceneTree
## Visual review tool for the menu motion. Windowed:
##   godot --windowed --path . --script tools/visual/capture_ui_motion.gd -- --out <prefix> --size 390x844
## Writes, for a win and for a loss of the week result sheet:
## <out>_win_mid.png (about 60 ms in, mid fade and rise), <out>_win_rest.png (settled),
## <out>_loss_mid.png, <out>_loss_rest.png. Never touches a real save.

var _w := 390
var _h := 844


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	var out := "ui_motion"
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
	state.save_path = "user://capture_ui_motion.save"
	state.settings_path = "user://capture_ui_motion.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	state.show_real_names = false
	UK.apply_appearance("dark")
	root.size = Vector2i(_w, _h)
	DisplayServer.window_set_size(Vector2i(_w, _h))
	feel.force_phone = true
	for win in [true, false]:
		var tag := "win" if win else "loss"
		state.reset()
		state.replay_seed = 2027
		state.start_season("COL", db.club_list("COL"))
		state.advance()
		var res: Dictionary = state.last_match
		var me := 0 if str(res["home"]) == state.my_club else 1
		var goals := [10, 10]
		var behinds := [5, 5]
		goals[me] = 13 if win else 8
		goals[1 - me] = 8 if win else 13
		res["goals"] = goals
		res["behinds"] = behinds
		res["score"] = [goals[0] * 6 + behinds[0], goals[1] * 6 + behinds[1]]
		state.last_match = res
		var rest: Array = []
		for r in state.last_results:
			rest.append(res if state.is_my_match(r) else r)
		state.last_results = rest
		var pid := str((res["roster"][me] as Array)[0]["id"])
		state.last_injuries = [{"club": state.my_club, "id": pid, "kind": "Hamstring", "weeks": 3}]
		state.last_mro = [{"club": state.my_club, "id": "", "name": "Test Player", "outcome": "suspension", "weeks": 2}]
		var hub = load("res://scenes/HubScene.tscn").instantiate()
		root.add_child(hub)
		await _frames(10)
		await create_timer(1.0).timeout
		feel.clear()
		hub.call("_show_results", state.last_results)
		await create_timer(0.06).timeout
		await _save("%s_%s_mid.png" % [out, tag])
		await create_timer(1.4).timeout
		await _save("%s_%s_rest.png" % [out, tag])
		print(tag, " Feel.moved: ", feel.moved)
		hub.queue_free()
		await _frames(4)
	quit(0)


func _save(path: String) -> void:
	await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if img.save_png(path) != OK:
		push_error("could not save " + path)
	print("wrote ", path)
