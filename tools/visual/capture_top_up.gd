extends SceneTree
## Essendon's 2016 top-up sheet for the director's look, on a phone: you coach
## Essendon, a dozen players are banned, ten spots wait. Never touches a real save.
##   godot --path . --script tools/visual/capture_top_up.gd -- --out PREFIX [--size 390x844]
## Writes <prefix>_open.png (nobody signed) and <prefix>_one.png (one signed).

var W := 390
var H := 844


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(path: String) -> void:
	await _frames(30)
	root.get_viewport().get_texture().get_image().save_png(path)
	print("wrote ", path)


func _run() -> void:
	var out := "top_up"
	var cli := OS.get_cmdline_user_args()
	for i in range(cli.size() - 1):
		match str(cli[i]):
			"--out": out = str(cli[i + 1])
			"--size":
				var wh := str(cli[i + 1]).split("x")
				W = int(wh[0])
				H = int(wh[1])
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://capture_top_up.save"
	gs.settings_path = "user://capture_top_up.cfg"
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(W, H))
	await _frames(10)
	var layout = root.get_node("ScreenLayout")
	layout.ui_scale = 1.0 / maxf(1.0, layout.desktop_density(Vector2(root.size), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0))
	layout._update_scale()
	await _frames(10)

	var ye = load("res://scripts/sim/YearEvents.gd")
	var md = load("res://scripts/state/MidseasonDraft.gd")
	gs.reset()
	gs.set_setting("seen_weekly_loop_intro", true)
	gs.career_seed = 2016
	gs.replay_seed = 2016
	gs.start_season("ESS", root.get_node("GameDB").club_list("ESS"))
	gs.week_events = []
	ye.state(gs)["top_up"] = {"year": gs.season_year, "club": "ESS", "left": 10, "most": 10, "signed": []}
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _frames(30)
	var sheet = hub.get_node_or_null("TopUpSheet")
	if sheet == null:
		push_error("capture_top_up: no top-up sheet over the hub")
		quit(1)
		return
	await _shot("%s_open.png" % out)
	var pool: Array = md.pool(gs)
	var sign = sheet.find_child("TopUpSign_%s" % str(pool[0]["id"]), true, false)
	sign.emit_signal("pressed")
	await _frames(10)
	await _shot("%s_one.png" % out)
	quit()
